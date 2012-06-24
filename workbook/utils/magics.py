# IPython imports
from IPython.core.displaypub import publish_display_data
from IPython.core.display import display
from IPython.core.magic import (Magics, magics_class, cell_magic, line_magic,
                                line_cell_magic)
from IPython.testing.skipdoctest import skip_doctest
from IPython.core.magic_arguments import (
    argument, magic_arguments, parse_argstring
)

# Local imports
from workbook.api import counter
from cell_question import (CellQuestion, 
                           MultipleChoiceQuestion,
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
        '--max_points', 
        default=1,
        type=int,
        help='Max points for a question.'
        )
    @argument(
        '--max_tries',
        default=1,
        type=int,
        help='Maximum number of times a user is allowed to try a question.'
        )
        
    @cell_magic
    def wb_multiple_choice(self, line, cell):
        """
        Create a multiple choice question. The cell
        must have variables 'choices' and 'correct_answer' defined.

        The check_answer just returns whether answer['answer'] == correct_answer
        
        """

        # parse the string
        args = parse_argstring(self.wb_multiple_choice, line)

        # when we save notebook of each student, we put a user_id into the namespace
        # here, we get it if it exists; otherwise we read it from the arguments
        if 'user_id' in self.shell.user_ns:
            user_id = self.shell.user_ns['user_id']
        else:
            user_id = args.user_id

        # generate question and attach shell
        question = MultipleChoiceQuestion(cell_input=cell,
                                      user_id=user_id,
                                      identifier=args.identifier,
                                      max_points=args.max_points,
                                      max_tries=args.max_tries,
                                      shell=self.shell)
        
        if args.seed is None:
            if 'seed' in self.shell.user_ns:
                seed = int(self.shell.user_ns['seed'])
            else:
                seed = 2
        # this should trigger generate_cell_outputs in CellQuestion
        question.seed = seed

        # not sure what this is for  --DS
        cell = question.form_cell(seed)

        question_types[args.identifier] = question

    @cell_magic
    def wb_true_false(self, line, cell):
        cell += "\nchoices=['True', 'False']\n"
        self.wb_multiple_choice(line, cell)

    @line_cell_magic
    def wb_grade_cell(self, line, cell=None):
        "Publish some latex."

        if cell is None:
            cell = ''

        # parse the string
        args = parse_argstring(self.wb_multiple_choice, line)

        # when we save notebook of each student, we put a user_id into the namespace
        # here, we get it if it exists; otherwise we read it from the arguments
        if 'user_id' in self.shell.user_ns:
            user_id = self.shell.user_ns['user_id']
        else:
            user_id = args.user_id

        # add identifier and max_points to the cell
        # (may be removed once we have ability to set cell metadata using magic)
        cell = ("identifier = '%s' \n" % args.identifier) + ('max_points = %d \n' % args.max_points) + cell

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

        question_types[args.identifier] = grade


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

