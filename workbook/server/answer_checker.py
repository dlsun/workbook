# IPython shell to check answers

import os, glob
from workbook.converters import ConverterNotebook
import IPython.nbformat.current as nbformat
from workbook.utils.questions import (find_identified_cells,
                                      find_identified_outputs,
                                      question_types,
                                      construct_question)
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

def check_answer(cell, user):
    question = question_types[cell['metadata']['identifier']]

    return question.check_answer(cell, user)

