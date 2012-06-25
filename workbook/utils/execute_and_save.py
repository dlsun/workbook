#!/usr/bin/env python
"""
simple example script for running and testing notebooks.

Usage: `ipnbdoctest.py foo.ipynb [bar.ipynb [...]]`

Each cell is submitted to the kernel, and the outputs are compared with those stored in the notebook.
"""

import os, sys, uuid, json

from Queue import Empty

from IPython.zmq.blockingkernelmanager import BlockingKernelManager
from IPython.nbformat.current import read, reads, NotebookNode, write

from workbook.io import *

# for testing only
import sys

def run_cell(cell_input, user_variables=None, user_expressions=None):

#    returned_user_variables = {}
    returned_user_expressions = {}
    shell.execute(cell_input, user_variables=user_variables, user_expressions=user_expressions)
    # wait for finish, maximum 20s
    shell_msg = shell.get_msg(timeout=20)
    outs = []
    
    while True:
        try:
            msg = iopub.get_msg(timeout=0.2)
        except Empty:
            break
        msg_type = msg['msg_type']
        if msg_type in ('status', 'pyin'):
            continue
        elif msg_type == 'clear_output':
            outs = []
            continue

        content = msg['content']
        # print msg_type, content
        out = NotebookNode(output_type=msg_type)
        
        if msg_type == 'stream':
            out.stream = content['name']
            out.text = content['data']
        elif msg_type in ('display_data', 'pyout'):
            for mime, data in content['data'].iteritems():
                attr = mime.split('/')[-1].lower()
                # this gets most right, but fix svg+html, plain
                attr = attr.replace('+xml', '').replace('plain', 'text')
                setattr(out, attr, data)
            if msg_type == 'pyout':
                out.prompt_number = content['execution_count']
        elif msg_type == 'pyerr':
            out.ename = content['ename']
            out.evalue = content['evalue']
            out.traceback = content['traceback']
        else:
            print "unhandled iopub msg:", msg_type
        
        outs.append(out)

    if 'user_variables' in shell_msg['content'].keys():
        returned_user_variables = shell_msg['content']['user_variables']
        for key, value in returned_user_variables.items():
            returned_user_variables[key] = eval(value)
        #if returned_user_variables:
        #    sys.stderr.write(str(returned_user_variables) + '\n\n')

    if 'user_expressions' in shell_msg['content'].keys():
        returned_user_expressions.update(shell_msg['content']['user_expressions'])

    return outs, returned_user_variables, returned_user_expressions
    

km = BlockingKernelManager()
km.session.key = uuid.uuid4()
km.start_kernel(extra_arguments=['--pylab=inline'], stderr=open(os.devnull, 'w'))
km.start_channels()
shell = km.shell_channel
iopub = km.sub_channel

def execute_notebook(nb, header_input=''):
    # run %pylab inline, because some notebooks assume this
    # even though they shouldn't
    km.shell_channel.execute("pass")
    km.shell_channel.get_msg()
    while True:
        try:
            km.sub_channel.get_msg(timeout=1)
        except Empty:
            break
    
    successes = 0
    failures = 0
    errors = 0
    prompt_number = 1
    for ws in nb.worksheets:
        for cell in ws.cells:
            cell.prompt_number = prompt_number
            # to check if a cell contains a question, we look for homework magic at beginning of input box
            if cell.cell_type == 'code':
                # set ownership of all existing code cells to instructor
                # (maybe we should do this for all cells, not just code cells?)
                cell.metadata.update( {'owner': 'workbook',
                                       'group': 'teacher'
                                       })
                if ''.join(cell.input).strip()[:4] == '%%wb':
                    try:
                        run_cell(header_input)
                        outs, user_vars = run_cell(cell.input, user_variables = ['identifier',
                                                                                 'max_points',
                                                                                 'max_tries'])[:-1]
                        if 'identifier' in user_vars:
                            import sys; sys.stderr.write('Now generating question: ' + user_vars['identifier'] + '\n')
                            cell.metadata.update( {'identifier': user_vars['identifier']} )
                        if 'max_points' in user_vars:
                            cell.metadata.update( {'max_points': user_vars['max_points']} )
                        if 'max_tries' in user_vars:
                            cell.metadata.update( {'max_tries': user_vars['max_tries']} )
                        cell.metadata.update( {'points': 0, 
                                               'tries': 0, 
                                               'correct': False,
                                               } )
                    except Exception as e:
                        print "failed to run cell:", repr(e)
                        print cell.input
                        errors += 1
                else:
                    try:
                        run_cell(header_input)
                        outs, user_vars = run_cell(cell.input)[:-1]
                    except Exception as e:
                        print "failed to run cell:", repr(e)
                        print cell.input
                        errors += 1
                cell.outputs = outs
                prompt_number += 1

def execute_and_save(ipynb, student_info):
    seed = student_info['seed']
    header_input = 'seed=%d; user_id="%s"' % (seed, student_info['id'])
    nb = read(open(ipynb, 'rb'), 'json')
    execute_notebook(nb, header_input=header_input)
    write(nb, open(ipynb, 'wb'), 'json')


if __name__ == '__main__':
    for ipynb in sys.argv[1:]:
        print "executing %s" % ipynb
        execute_and_save(ipynb)
