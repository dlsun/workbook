
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

from IPython.extensions.rmagic import RMagics

# Numpy imports

import numpy as np

# Rpy2 imports

import rpy2.rinterface as ri
import rpy2.robjects as ro
from rpy2.robjects.numpy2ri import numpy2ri
ro.conversion.py2ri = numpy2ri

# Local imports

from .questions import publish_workbook_metadata

@magics_class
class HomeworkMagics(RMagics):

    def __init__(self, shell, lookup_questions):
        self.answers = {}
        self.questions = {}
        self.lookup_questions = lookup_questions
        super(HomeworkMagics, self).__init__(shell)
        self.cache_display_data = True
        self.counter = 1

    @magic_arguments()
    @argument(
        'number', 
        type=int,
        help='Which question do I generate?'
        )
    @argument(
        '-f', '--force',
        default=False,
        action='store_true',
        help='Force a new question to be generated.'
        )
    @cell_magic
    def Question(self, line, cell):
        "Generate a question"
        args = parse_argstring(self.Question, line)
        if args.number not in self.questions.keys() or args.force:  
            question_dict, question_data = self.lookup_questions[args.number]()
            self.questions[args.number] = (question_dict, question_data)
        else:
            question_dict = self.questions[args.number][0]

        for mime, data in question_dict:
            if mime == 'Rplot': # a signal to create an Rplot
                line, cell = data
                self.R(line, cell)
            publish_display_data('HomeworkMagics', {mime:data})

    @magic_arguments()
    @argument(
        'name_of_dict', 
        type=str,
        )
    @line_magic
    def metadata(self, line):
        """
        Publish elements of a dictionary into workbook_metadata of the current cell
        """
        args = parse_argstring(self.metadata, line)
        metadata = self.shell.user_ns[args.name_of_dict]
        publish_workbook_metadata(metadata)

    @argument(
        'number', 
        type=int
        )
    @magic_arguments()
    @argument(
        'part', 
        default=None,
        nargs='?'
        )
    @argument(
        '-R', 
        default=False,
        action='store_true',
        help='Execute this block of code in R and publish the result.'
        )
    @cell_magic
    def Answer(self, line, cell):
        "Answer to question, it is appended to the current answer for that question "
        args = parse_argstring(self.Answer, line)
        answer_text = cell
        self.answers.setdefault(args.number, {})
        if args.part is None:
            try:
                part = max(self.answers[args.number].keys()) + 1
            except ValueError:
                part = 0
        else:
            part = int(args.part)
        if not args.R:
            self.answers[args.number][part] = [('HomeworkMagic.R', {'text/latex':cell})]
            publish_display_data('HomeworkMagic.R', {'text/latex':cell})
        else:
            self.answers[args.number][part] = [('HomeworkMagic.R', {'text/html':r'<h2>R code</h2>'}),
                                               ('HomeworkMagic.R', {'text/plain':cell})]
            self.R('', cell)
            # copy the display data for later -- maybe possible with IPython.core.displayhook?
            self.answers[args.number][part] += copy(self.display_cache)

    @magic_arguments()
    @argument(
        'number', 
        type=int
        )
    @cell_magic
    def View(self, line, cell):
        "Answer to question, it is appended to the current answer for that question "
       
        args = parse_argstring(self.View, line)

        # First, republish the question

        publish_display_data("HomeworkMagic.R", {'text/html':r'<h2>Question</h2>'})            

        self.Question(line, cell)

        publish_display_data("HomeworkMagic.R", {'text/html':r'<h2>Answer</h2>'})            

        for k in self.answers[args.number].keys():
            for tag, mime_data in self.answers[args.number][k]:
                publish_display_data(tag, mime_data)

    @magic_arguments()
    @argument(
        'number', 
        type=int
        )
    @cell_magic
    def MultipleChoiceSetup(self, line, cell):
        """Multiple choice question setup.

        """
       
        args = parse_argstring(self.MultipleChoiceSetup, line)
        number = args.number
        # First, republish the question

        publish_display_data("HomeworkMagic.R", {'text/html':r'<h2>Question %d</h2>' % int(number)})            

        self.R(line, cell)


    @magic_arguments()
    @argument(
        'number', 
        type=int
        )
    @cell_magic
    def MultipleChoiceQuestion(self, line, cell):
        """Multiple choice question.
        Within the cell, you must define a sequence named "choices"
        and a string named "question_text"
        """
       
        args = parse_argstring(self.MultipleChoiceQuestion, line)
        number = args.number

        self.shell.ex(cell)
        # get the question_text
        try:
            question_text = self.shell.user_ns['question_text']
        except:
            raise ValueError('Need some some text for the question! Make a string named "question_text".')

        publish_display_data("HomeworkMagic.R", {'text/latex':question_text})

        # get the choices
        try:
            choices = self.shell.user_ns['choices']
        except:
            raise ValueError('Need some choices for the answer! Make a sequence named "choices".')

        # shuffle the choices
        np.random.shuffle(choices)

        h = md5()
        h.update(cell)
        name = h.hexdigest()
        radio_code = '\n'.join(['''
        <input type="radio" name="%(name)s" value="%(value)s"> %(value)s<br>
        ''' % {'name':name, 'value':choice} for choice in choices])

        publish_display_data("HomeworkMagic.R", {'text/html':radio_code}, metadata={'md5':'testmeta'})



debug = True
def question1():
    a, b = sorted(np.random.random_integers(0, 10, size=(2,)))
    if debug: # just to write the notebook without the random numbers for now...
        a, b = (4, 9)
    if a == b:
        b = a + np.random.random_integers(0, 10)
    question_text = r'What is $\int_%d^%d x^2 - 3x \; dx$?' % (a, b)
    return [('text/latex', question_text)], (a,b)

def question2():
    X, Y = np.random.standard_normal([2,100])
    Y += X
    ip.user_ns['X'] = X
    ip.user_ns['Y'] = Y
    return [('Rplot', (' -i X -i Y', 'plot(X, Y, pch=23, bg="red", cex=2)')),
            ('text/latex', r'Is $\text{Cor}(X,Y)$ positive or negative? Give a rough estimate.')], {'X':X, 'Y':Y}

lookup = {1:question1,
          2:question2}

ip = get_ipython()
hwmagic = HomeworkMagics(ip, lookup)
ip.register_magics(hwmagic)

