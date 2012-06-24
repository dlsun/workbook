import json, sys
import datetime, time # for timestamping instances
from workbook.io import *
from IPython.utils import traitlets as traits

question_types = {}
question_instances = {}

import IPython.nbformat.current as nbformat
from workbook.utils.execute_and_save import shell, run_cell as km_run_cell

# wrapper around the kernel's run_cell
def run_cell(cell_input, shell=None, user_variables=[]):
    if shell is not None:
        shell.run_cell(cell_input)
    return km_run_cell(cell_input, user_variables=user_variables)


class CellQuestion(traits.HasTraits):

    cell_input = traits.Unicode
    user_id = traits.Unicode
    identifier = traits.Unicode
    max_points = traits.Int
    max_tries = traits.Int
    seed = traits.Int
    metadata = traits.Dict # this should be removed
    answer = traits.Unicode
    shell = traits.Any(None)

    # the different outputs
    cell_outputs = traits.List
    cell_comments = traits.List

    def __init__(self, **kw):
        # initialize some traits
        traits.HasTraits.__init__(self, **kw)

        # set header information
        header_input = ("identifier = '%s' \n" % self.identifier) + ("max_points = %d \n" % self.max_points) + \
            ("max_tries = %d \n" % self.max_tries)
        run_cell(header_input, shell = self.shell)

        # set event handlers
        self.on_trait_change(self.update_seed, ['seed'])
        self.on_trait_change(self.generate_cell_outputs, ['seed'])
        self.timestamp = datetime.datetime(*time.localtime()[:6])
        question_instances[(self.identifier, self.user_id)] = self
    
    def _shell_changed(self):
        run_cell('\n'.join(['%load_ext rmagic',
                            'from IPython.core.displaypub import publish_display_data',
                            'import numpy as np, random, json']),
                 shell=self.shell)
    
    def update_seed(self):
        """
        Set the seed in the shell by creating a 'cell' and running it.
        """
        cell_input = '\n'.join(['seed=%d' % self.seed,
                                'np.random.seed(seed); random.seed(seed)',
                                '%R -i seed set.seed(seed); rm(seed)', ''])
        run_cell(cell_input, shell=self.shell)
    
    def generate_cell_outputs(self):
        """
        runs the cell_input through the shell and prints output

        NB. This method probably needs to be overridden in subclasses.
        """
        # store the identifier and max_points
        self.cell_outputs, variables = \
            run_cell(self.cell_input,shell=self.shell)[:2]
    
    def form_cell(self, seed, shell=None):
        self.seed = seed; self.update_seed()
        cell = nbformat.new_code_cell(input=self.cell_input, 
                                      outputs=self.cell_outputs)
        self.metadata.update(cell.metadata)
        return cell
    
    def retrieve_seed(self):
        return json.load(open(os.path.join(PATH_TO_HW_FILES,
                                           self.user_id, 
                                           "student_info.json"), 'rb'))['seed']

    def check_answer(self, cell_dict):
        """
        checks answer and returns a new cell
        """
        raise NotImplementedError


class MultipleChoiceQuestion(CellQuestion):

    choices = traits.List
    correct_answer = traits.Unicode

    def __init__(self, **kw):
        CellQuestion.__init__(self, **kw)
        self.on_trait_change(self.validate_answer, ['answer'])

    def generate_cell_outputs(self):

        # store the correct answer for checking later
        self.cell_outputs, variables = \
            run_cell(self.cell_input, 
                     user_variables=['correct_answer','choices'], 
                     shell=self.shell)[:2]

        # no need to eval()...that's taken care of in run_cell now        
        self.choices = variables['choices']
        self.correct_answer = variables['correct_answer']
        self.answer = ''

        # instructions to generate the form
        if self.answer:
            checked = self.answer
        else:
            checked = ''
        choices = self.choices

        d = {'identifier': self.identifier }
        buttons = []
        for choice in choices:
            d['value'] = choice
            if choice == checked and checked:
                buttons.append("""<p><input type="radio" name="%(identifier)s" value="%(value)s" id="%(value)s" checked="checked"> %(value)s</p>""" % d)
            else:
                buttons.append("""<p><input type="radio" name="%(identifier)s" value="%(value)s" id="%(value)s"> %(value)s</p>""" % d)
        html = ('<form name="%(identifier)s" method="post" >\n' % d) + '\n'.join(buttons) + '</form>\n'

        form_input = '\n'.join(["publish_display_data('CellQuestion', {'text/latex':question_text})",
                                "publish_display_data('CellQuestion', {'text/html':'''%s'''})" % html]) 
        
        self.cell_outputs += run_cell(form_input, shell=self.shell)[0]
    
 
    comments = {True: "<h2>Good job. Points: %(points)d / %(max_points)d</h2>.",
                False: "<h2>Try again. Points: %(points)d / %(max_points)d. You have used %(tries)d of %(max_tries)d tries.</h2>"}
    def generate_comments(self):
        self.cell_comments = html_outputs(self.shell, self.comments[self.metadata['correct']] % self.metadata)
 
    def validate_answer(self):
        if self.answer:
            correct = (self.answer == self.correct_answer)
            self.metadata['correct'] = correct
            self.metadata['points'] = (self.max_points if correct else 0)
            self.metadata['max_points'] = self.max_points
            self.generate_comments()

    def check_answer(self, cell_dict):
        cell = nbformat.NotebookNode(**cell_dict)

        # get seed and add trial number to it
        seed = self.retrieve_seed()
        cell.metadata.setdefault('tries', 0)
        self.metadata.update(cell.metadata)
        seed += cell.metadata['tries']
        self.seed = seed; self.update_seed()
         
        # append the answer to the answer history
        cell.metadata.setdefault('answer_history', [])
        cell.metadata['answer_history'].append(cell.metadata['answer'])
        self.metadata.update(cell.metadata)

        # if the user has not used up all the allowed tries
        if self.metadata['tries'] < self.metadata['max_tries']:
 
            # increment tries count by 1
            cell.metadata['tries'] += 1
            self.metadata.update(cell.metadata)

           # this should trigger validate_answer
            self.answer = cell.metadata['answer']
 
           # generate new question if incorrect
            if not self.metadata['correct']:
                self.seed += 1
            # add the comments to the outputs
            cell.outputs = self.cell_outputs + self.cell_comments
            # sync the cell metadata with the server metadata

        else:
            cell_comments = html_outputs(self.shell, "<h2>Sorry, but you've used up all %(max_tries)d tries for this question. Points: %(points)d / %(max_points)d</h2>" % self.metadata)
            cell.outputs = self.cell_outputs + cell_comments

        cell.metadata.update(self.metadata)

        return cell



class TAGrade(CellQuestion):

    def form_cell(self, seed, metadata={}):
        outputs, cell_metadata = run_cell(self.cell_input, 
                                          user_variables=['identifier',
                                                          'comments',
                                                          'points',
                                                          'max_points'],
                                          shell=self.shell)[:2]
        comment_outputs = html_outputs(self.shell, '''<h3>%(comments)s\nPoints: %(points)d/%(max_points)d</h3>''' % cell_metadata)
        cell_metadata['identifier'] = self.identifier
        cell = nbformat.new_code_cell(input=self.cell_input,
                                      outputs=outputs + comment_outputs,
                                      metadata=cell_metadata)
        self.metadata.update(cell.metadata)
        return cell

    def check_answer(self, cell_dict, user):
        cell = nbformat.NotebookNode(**cell_dict)
        return cell

def html_outputs(shell, *raw_html_bits):
    return run_cell('\n'.join(["""publish_display_data("CellQuestion", {"text/html":'''%s'''})""" % raw_html for raw_html in raw_html_bits]), shell=shell)[0]

def latex_outputs(shell, *raw_latex_bits):
    return run_cell('\n'.join(["""publish_display_data("CellQuestion", {"text/latex":r'''%s'''})""" % raw_latex for raw_latex in raw_latex_bits]), shell=shell)[0]

