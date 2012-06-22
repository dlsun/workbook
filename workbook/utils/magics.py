
import sys
import tempfile
from glob import glob
from shutil import rmtree
from copy import copy
from md5 import md5

# IPython imports
from IPython.core.displaypub import publish_display_data
from IPython.core.display import display
from IPython.core.magic import (Magics, magics_class, cell_magic, line_magic,
                                line_cell_magic)
from IPython.testing.skipdoctest import skip_doctest
from IPython.core.magic_arguments import (
    argument, magic_arguments, parse_argstring
)

# Numpy imports

import numpy as np

# Local imports

from workbook.api import counter
from cell_question import (CellQuestion, 
                           MultipleChoiceCell,
                           TAGrade,
                           question_types, 
                           question_instances)

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
        default=None,
        help='Random seed to set.'
        )
    @argument(
        '--user_id', 
        default='server',
        help='Default user.'
        )
    @argument(
        '--practice', 
        default=False,
        action='store_true',
        help='Should the question be a practice (i.e. regenerated over and over)'
        )
    @cell_magic
    def wb_question(self, line, cell):
        "Generate a question after setting seed=seed+trial."
        args = parse_argstring(self.wb_question, line)
        # later, we put a user_id into the namespace
        # while saving notebook of each student -- a bit of a hack
        if 'user_id' in self.shell.user_ns:
            user_id = self.shell.user_ns['user_id']
        else:
            user_id = args.user_id

        question = CellQuestion(cell_input=cell, identifier=args.identifier,
                                number=counter.question_number,
                                user_id=user_id)
        question.shell = self.shell 

        if args.seed is None:
            if 'seed' in self.shell.user_ns:
                seed = int(self.shell.user_ns['seed'])
            else:
                seed = 2
        question.seed = seed

        cell = question.form_cell(seed)
        question_types[args.identifier] = question

    @line_cell_magic
    def wb_grade_cell(self, line, cell=None):
        "Publish some latex."

        if cell is None:
            cell = ''


        args = parse_argstring(self.wb_question, line)

        # we have to make sure this is the student's id so it gets attached
        # in the correct place
        if 'user_id' in self.shell.user_ns:
            user_id = self.shell.user_ns['user_id']
        else:
            user_id = args.user_id

        grade = TAGrade(cell_input=cell, identifier=args.identifier,
                        user_id=user_id)
        grade.shell = self.shell 
        if args.seed is None:
            if 'seed' in self.shell.user_ns:
                seed = int(self.shell.user_ns['seed'])
            else:
                seed = 2
        grade.seed = seed
        cell = grade.form_cell(seed)

    @cell_magic
    def wb_multiple_choice(self, line, cell):
        """
        Create a multiple CellQuestion. The cell
        must have variables 'choices' and 'correct_answer' defined.

        The check_answer just returns whether answer['answer'] == correct_answer
        
        """
        args = parse_argstring(self.wb_question, line)

        # later, we put a user_id into the namespace
        # while saving notebook of each student -- a bit of a hack
        if 'user_id' in self.shell.user_ns:
            user_id = self.shell.user_ns['user_id']
        else:
            user_id = args.user_id

        question = MultipleChoiceCell(cell_input=cell, 
                                      identifier=args.identifier, 
                                      practice=args.practice,
                                      number=counter.question_number,
                                      user_id=user_id)
        question.shell = self.shell 
        if args.seed is None:
            if 'seed' in self.shell.user_ns:
                seed = int(self.shell.user_ns['seed'])
            else:
                seed = 2
        question.seed = seed
        cell = question.form_cell(seed)
        question_types[args.identifier] = question

    @cell_magic
    def wb_true_false(self, line, cell):
        cell += "\nchoices=['True', 'False']\n"
        self.wb_multiple_choice(line, cell)

# register the magic

ip = get_ipython()
hwmagic = HomeworkMagics(ip)
ip.register_magics(hwmagic)

def wb_latex(text):
    publish_display_data("HomeworkMagic", {'text/latex':text})

def publish_workbook_metadata(metadata):
    publish_display_data("HomeworkBuilder", 
                         {"application/json":{"workbook_metadata":
                                                  metadata}})

