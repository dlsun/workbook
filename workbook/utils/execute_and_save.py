#!/usr/bin/env python
"""
simple example script for running and testing notebooks.

Usage: `ipnbdoctest.py foo.ipynb [bar.ipynb [...]]`

Each cell is submitted to the kernel, and the outputs are compared with those stored in the notebook.
"""

import os, sys, uuid

from Queue import Empty

from IPython.zmq.blockingkernelmanager import BlockingKernelManager
from IPython.nbformat.current import reads, NotebookNode

from workbook.external.nbconvert import ConverterNotebook

def run_cell(km, cell):
    shell = km.shell_channel
    iopub = km.sub_channel
    # print "\n\ntesting:"
    # print cell.input
    shell.execute(cell.input)
    # wait for finish, maximum 20s
    shell.get_msg(timeout=20)
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

    return outs
    

km = BlockingKernelManager()
km.session.key = uuid.uuid4()
km.start_kernel(extra_arguments=['--pylab=inline'], stderr=open(os.devnull, 'w'))
km.start_channels()

def execute_notebook(nb):
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
            if cell.cell_type != 'code':
                continue
            try:
                outs = run_cell(km, cell)
            except Exception as e:
                print "failed to run cell:", repr(e)
                print cell.input
                errors += 1
                continue
            cell.outputs = outs
            prompt_number += 1
    # km.shutdown_kernel()
    # del km

def execute_and_save(ipynb):
    converter = ConverterNotebook(ipynb, os.path.splitext(ipynb)[0] + '_executed')
    converter.read()
    execute_notebook(converter.nb)    
    return converter.render()


if __name__ == '__main__':
    for ipynb in sys.argv[1:]:
        print "executing %s" % ipynb
        execute_and_save(ipynb)
