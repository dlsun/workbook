# IPython shell to check answers

import os, glob
from workbook.converters import ConverterNotebook
import IPython.nbformat.current as nbformat
from workbook.utils.questions import (find_identified_cells,
                                      find_identified_outputs,
                                      update_output,
                                      question_types)
from workbook.io import *

from IPython.frontend.terminal.interactiveshell import TerminalInteractiveShell

def initialize_shell():
    shell = TerminalInteractiveShell()
    for ipynb in glob.glob(os.path.join(PATH_TO_HW_TEMPLATES, '*ipynb')):
        nb = nbformat.read(open(ipynb, 'rb'), 'json')
        for ws in nb.worksheets:
            for cell in ws.cells:
                if hasattr(cell, 'input'):
                    shell.run_cell(cell.input)
    return shell

def find_question_types():
    shell = initialize_shell()
    curdir = os.path.abspath(os.curdir)
    shell.run_cell('import workbook.utils.questions as wq')
    wq = shell.user_ns['wq']
    nm = wq.question_types['normal_mean']('test',3,4,5)
    os.chdir(curdir)
    return wq.question_types

def update_question_types():
    question_types.update(find_question_types())

question_types_already_found = False
def check_answer(filename, identifier, answer):
#     global question_types_already_found
#     if not question_types_already_found:
#         update_question_types()
#         question_types_already_found = True

    tmpf = os.path.splitext(filename)[0] + '_tmp'
    converter = ConverterNotebook(filename, tmpf)
    converter.read()

    cells = find_identified_cells(converter.nb, identifier)
    if len(cells) > 1:
        raise ValueError('more than one match: %s' % '\n'.join([str(c) for c in cells]))
    outputs = find_identified_outputs(cells[0], identifier)
    for output in outputs:
        update_output(output, identifier, answer)

    outfile = converter.render()
    os.rename(outfile, filename)
    return filename
