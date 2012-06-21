import json
from workbook.io import *
from IPython.utils import traitlets as traits

question_types = {}

import IPython.nbformat.current as nbformat
from workbook.utils.execute_and_save import shell, run_cell as km_run_cell

def run_cell(cell_input, shell=None, user_variables=[]):
    if shell is not None:
        shell.run_cell(cell_input)
    return km_run_cell(cell_input, user_variables=user_variables)

class CellQuestion(traits.HasTraits):

    answer_buffer = traits.Dict
    cell_input = traits.Unicode
    identifier = traits.Unicode
    seed = traits.Int
    user_id = traits.Unicode
    user_name = traits.Unicode
    number = traits.Int

    outputs = traits.List
    num_outputs = traits.Int(1) # how many outputs does the answer checking form

    comments = traits.Dict({True:"<h2> Good job. Points: %(points)d / %(max_points)d </h2>",
                            False:"<h2> Try again. Points: %(points)d / %(max_points)d</h2>"})

    practice_comments = traits.Dict({True:"<h2> Good job. Here's another. Points: %(points)d / %(max_points)d </h2>",
                            False:"<h2> Try again. Here's another. Points: %(points)d / %(max_points)d</h2>"})

    points = traits.Dict({True:1,
                          False:0,
                          'max':1})

    practice = traits.Bool(False)

    def __init__(self, **kw):
        self.on_trait_change(self.update_seed, ['seed'])
        traits.HasTraits.__init__(self, **kw)

    def update_seed(self):
        cell_input = '\n'.join(['seed=%d' % self.seed,
                                '%load_ext rmagic',
                                'from IPython.core.displaypub import publish_display_data',
                                'import numpy as np, random, json',
                                'np.random.seed(seed); random.seed(seed)',
                                '%R -i seed set.seed(seed); rm(seed)', ''])
        run_cell(cell_input, shell=self.shell)

    def form_cell(self, seed, metadata={}):
        self.seed = seed; self.update_seed()
        if 'answer' in metadata:
            self.answer = metadata['answer']
        outputs, variables = run_cell(self.cell_input, 
                                      user_variables=['correct_answer'],
                                      shell=self.shell)[:2]
        # store the correct answer for checking later
        # need to manage the size of the answer_buffer
        self.answer_buffer[self.seed] = variables['correct_answer']

    def check_answer(self, cell_dict, user):
        cell = nbformat.NotebookNode(**cell_dict)
        seed = json.load(open(os.path.join(PATH_TO_HW_FILES,
                                           user['id'], 
                                           "student_info.json"), 'rb'))['seed']

        cell.metadata.setdefault('already_checked', False)
        cell.metadata.setdefault('trial_number', 0)

        seed += cell.metadata['trial_number']

        self.seed = seed; self.update_seed()

        # return a checked input
        # maybe we can just do this in javascript?
        # i.e. check the correct box on the form
        # if so, then we only need to store the answers
        # on the surver and not 
        # recompute the cell each timme

        if not self.practice: 
            self.answer = cell.metadata['answer']
        new_cell = self.form_cell(seed)
        new_cell.metadata.update(cell.metadata)
        cell = new_cell

        correct_answer = self.answer_buffer[seed]

        correct = cell.metadata['answer'] == correct_answer
        if not self.practice:
            cell.metadata['points'] = self.points[correct]
            cell.metadata['max_points'] = self.points['max']
        else:
            cell.metadata.setdefault('points', 0)
            cell.metadata.setdefault('max_points', 0)
            cell.metadata['points'] += self.points[correct]
            cell.metadata['max_points'] += self.points['max']
        cell.metadata['correct'] = correct

        if self.practice:
            cell['metadata']['trial_number'] += 1
            seed += 1
            new_cell = self.form_cell(seed)
            new_cell.metadata.update(cell.metadata)
            cell = new_cell

        if not cell.metadata['already_checked']:
            if not self.practice: 
                cell.outputs += html_outputs(self.shell, self.comments[correct] % cell.metadata)
            else:
                cell.outputs += html_outputs(self.shell, self.practice_comments[correct] % cell.metadata)
            cell.metadata['already_checked'] = True
        else:
            if not self.practice:
                cell.outputs = cell.outputs[:-self.num_outputs]
                cell.outputs += html_outputs(self.shell, self.comments[correct] % cell.metadata) 
            else:
                cell.outputs += html_outputs(self.shell, self.practice_comments[correct] % cell.metadata) 

        return cell

class TAGrade(CellQuestion):

    def form_cell(self, seed, metadata={}):
        outputs, cell_metadata = run_cell(self.cell_input, 
                                          user_variables=['comments',
                                                          'points',
                                                          'max_points'],
                                          shell=self.shell)[:2]
        for key, value in cell_metadata.items():
            cell_metadata[key] = eval(value)
        comment_outputs = html_outputs(self.shell, '''<h3>%(comments)s\nPoints: %(points)d/%(max_points)d</h3>''' % cell_metadata)
        cell_metadata['identifier'] = self.identifier
        cell = nbformat.new_code_cell(input=self.cell_input,
                                      outputs=outputs + comment_outputs,
                                      metadata=cell_metadata)
        return cell

    def check_answer(self, cell_dict, user):
        cell = nbformat.NotebookNode(**cell_dict)
        return cell

class MultipleChoiceCell(CellQuestion):

    question_text = traits.Unicode
    form = traits.Unicode
    choices = traits.List
    answer = traits.Unicode

    def __init__(self, **kw):
        self.setup_handlers()
        CellQuestion.__init__(self, **kw)

    def setup_handlers(self):
        self.on_trait_change(self.generate_form_input, ['answer', 'choices',
                                                        'identifier'])

    def generate_form_input(self):
        checked = self.answer
        choices = self.choices

        d = {'identifier': self.identifier }
        buttons = []
        for choice in choices:
            d['value'] = choice
            if choice == checked and checked is not None:
                buttons.append("""<p><input type="radio" name="%(identifier)s" value="%(value)s" id="%(value)s" checked="checked"> %(value)s</p>""" % d)
            else:
                buttons.append("""<p><input type="radio" name="%(identifier)s" value="%(value)s" id="%(value)s"> %(value)s</p>""" % d)
        radio_code = ('<form name="%(identifier)s" method="post" >\n' % d) + '\n'.join(buttons) + '</form>\n'

        form_input = '\n'.join(["publish_display_data('CellQuestion', {'text/latex':question_text})",
                                "publish_display_data('CellQuestion', {'text/html':'''%s'''})" % radio_code]) 
        self.form = form_input

    def form_cell(self, seed, metadata={}, shell=None):
        self.seed = seed; self.update_seed()
        outputs, variables = run_cell(self.cell_input, 
                                     user_variables=['correct_answer',
                                                     'choices',
                                                     'question_text'], shell=self.shell)[:2]

        # store the choices and correct answer for checking later

        self.choices = eval(variables['choices'])
        self.answer_buffer[seed] = eval(variables['correct_answer'])
        form_outputs = run_cell(self.form,
                                shell=self.shell)[0]
        cell = nbformat.new_code_cell(input=self.cell_input, outputs=outputs +
                                      form_outputs,
                                      metadata=metadata)
        return cell


def html_outputs(shell, *raw_html_bits):
    return run_cell('\n'.join(["""publish_display_data("CellQuestion", {"text/html":'''%s'''})""" % raw_html for raw_html in raw_html_bits]), shell=shell)[0]

def latex_outputs(shell, *raw_latex_bits):
    return run_cell('\n'.join(["""publish_display_data("CellQuestion", {"text/latex":r'''%s'''})""" % raw_latex for raw_latex in raw_latex_bits]), shell=shell)[0]

