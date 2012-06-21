import json
from md5 import md5
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
    number = traits.Int
    shell = traits.Any(None)
    md5 = traits.Unicode

    # the different outputs

    cell_outputs = traits.List
    form_outputs = traits.List
    comment_outputs = traits.List

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
        self.on_trait_change(self.set_md5, ['cell_input', 'identifier'])
        self.on_trait_change(self.generate_cell_outputs, ['seed'])
        traits.HasTraits.__init__(self, **kw)

    def _shell_changed(self):
        run_cell('\n'.join(['%load_ext rmagic',
                            'from IPython.core.displaypub import publish_display_data',
                            'import numpy as np, random, json']),
                 shell=self.shell)

    def set_md5(self):
        h = md5()
        h.update(self.cell_input + self.identifier)
        self.md5 = h.hexdigest()

    def update_seed(self):
        cell_input = '\n'.join(['seed=%d' % self.seed,
                                'np.random.seed(seed); random.seed(seed)',
                                '%R -i seed set.seed(seed); rm(seed)', ''])
        run_cell(cell_input, shell=self.shell)

    def generate_cell_outputs(self):
        self.cell_outputs, variables = run_cell(self.cell_input, 
                                                user_variables=['correct_answer'],
                                                shell=self.shell)[:2]
        # store the correct answer for checking later
        # need to manage the size of the answer_buffer
        self.answer_buffer[self.seed] = eval(variables['correct_answer'])


    def form_cell(self, seed, metadata={}):
        self.seed = seed; self.update_seed()
        if 'answer' in metadata:
            self.answer = metadata['answer']
            
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

        # append the answer to the answer history

        cell.metadata.setdefault('answer_history', [])
        cell.metadata['answer_history'].append(cell.metadata['answer'])

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
        CellQuestion.__init__(self, **kw)
        self.on_trait_change(self.generate_cell_outputs, ['seed'])
        self.on_trait_change(self.generate_form_input, ['answer', 
                                                        'choices',
                                                        'identifier'])
        self.on_trait_change(self.generate_form_outputs, ['form'])
        self.on_trait_change(self.generate_comment_outputs, ['answer'])
        self.setup_handlers()

    def generate_cell_outputs(self):
        # store the correct answer for checking later
        # need to manage the size of the answer_buffer
        self.cell_outputs, variables = \
            run_cell(self.cell_input, 
                     user_variables=['correct_answer',
                                     'choices',
                                     'question_text'], 
                     shell=self.shell)[:2]

        self.choices = eval(variables['choices'])
        self.answer_buffer[seed] = eval(variables['correct_answer'])

    def generate_form_input(self):
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
        radio_code = ('<form name="%(identifier)s" method="post" >\n' % d) + '\n'.join(buttons) + '</form>\n'

        form_input = '\n'.join(["publish_display_data('CellQuestion', {'text/latex':question_text})",
                                "publish_display_data('CellQuestion', {'text/html':'''%s'''})" % radio_code]) 
        self.form = form_input

    def generate_form_outputs(self):
        self.form_outputs = run_cell(self.form,
                                     shell=self.shell)[0]
        
    def form_cell(self, seed, metadata={}, shell=None):
        self.seed = seed; self.update_seed()
        cell = nbformat.new_code_cell(input=self.cell_input, 
                                      outputs=self.cell_outputs +
                                      self.form_outputs,
                                      metadata=metadata)
        cell.metadata['md5'] = self.md5
        return cell


def html_outputs(shell, *raw_html_bits):
    return run_cell('\n'.join(["""publish_display_data("CellQuestion", {"text/html":'''%s'''})""" % raw_html for raw_html in raw_html_bits]), shell=shell)[0]

def latex_outputs(shell, *raw_latex_bits):
    return run_cell('\n'.join(["""publish_display_data("CellQuestion", {"text/latex":r'''%s'''})""" % raw_latex for raw_latex in raw_latex_bits]), shell=shell)[0]

