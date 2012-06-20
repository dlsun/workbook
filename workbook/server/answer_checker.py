# IPython shell to check answers

import os, glob
from workbook.converters import ConverterNotebook
import IPython.nbformat.current as nbformat
from workbook.utils.cell_question import question_types
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

def check_answer(cell_dict, user):
    question = question_types[cell_dict['metadata']['identifier']]

    cell = question.check_answer(cell_dict, user)
    cell.input = user['cipher'].encrypt(cell['input'])
    cell.cell_type = 'workbook'
    import sys; sys.stderr.write(`cell`)
    return cell
