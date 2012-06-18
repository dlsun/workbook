
import sys
import tempfile
from glob import glob
from shutil import rmtree
from copy import copy
from md5 import md5

# IPython imports
from IPython.core.displaypub import publish_display_data
from IPython.core.magic import (Magics, magics_class, cell_magic, line_magic,
                                line_cell_magic)
from IPython.testing.skipdoctest import skip_doctest
from IPython.core.magic_arguments import (
    argument, magic_arguments, parse_argstring
)

# Numpy imports

import numpy as np

# Local imports

from .questions import publish_workbook_metadata, question_types
from cell_question import CellQuestion

@magics_class
class HomeworkMagics(Magics):

    @magic_arguments()
    @argument(
        'identifier', 
        help='Name of question.'
        )
    @argument(
        '--seed', 
        type=int,
        default=0,
        help='Random seed to set.'
        )
    @argument(
        '--trial',
        type=int,
        default=0,
        help='Which trial on this problem.'
        )
    @cell_magic
    def wb_question(self, line, cell):
        "Generate a question after setting seed=seed+trial."
        args = parse_argstring(self.wb_question, line)
        self.shell.user_ns['seed'] = args.seed + args.trial
        self.shell.run_cell('\n'.join(['import numpy as np, random',
                                       'np.random.seed(seed); random.seed(seed)']))
        self.shell.run_line_magic("R", " -i seed set.seed(seed); rm(seed)")
        self.shell.run_cell(cell)
        question = CellQuestion(cell, identifier)
        question_types[args.identifier] = question

    @line_cell_magic
    def wb_latex(self, line, cell=None):
        "Publish some latex."

        if cell is None:
            cell = ''
        publish_display_data("HomeworkMagic", {'text/latex':line + '\n' + cell})

    @cell_magic
    def wb_multiple_choice(self, line, cell):
        """
        Create a multiple CellQuestion. The cell
        must have variables 'choices' and 'correct_answer' defined.

        The check_answer just returns whether answer['answer'] == correct_answer
        
        """

        multiple_choice_check_answer = """
def check_answer(answer):
    if answer not in choices:
        raise ValueError('answer should be on of the choices: %s' % `(answer, choices)`)
    return answer == correct_answer
        """        cell = cell + multiple_choice_check_answer
        self.wb_question(line, cell)

    @magic_arguments()
    @argument(
        'name_of_dict', 
        type=str,
        )
    @line_magic
    def wb_metadata(self, line):
        """
        Publish elements of a dictionary into workbook_metadata of the current cell
        """
        args = parse_argstring(self.wb_metadata, line)
        metadata = self.shell.user_ns[args.name_of_dict]
        publish_workbook_metadata(metadata)

# register the magic

ip = get_ipython()
hwmagic = HomeworkMagics(ip)
ip.register_magics(hwmagic)

def wb_latex(text):
    publish_display_data("HomeworkMagic", {'text/latex':text})
