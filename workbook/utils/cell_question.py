import json, sys
import datetime, time # for timestamping instances
from md5 import md5
from workbook.io import *
from IPython.utils import traitlets as traits
import numpy as np

question_types = {}
question_instances = {}

import IPython.nbformat.current as nbformat
from workbook.utils.execute_and_save import shell, run_cell as km_run_cell

def run_cell(cell_input, shell=None, user_variables=[]):
    if shell is not None:
        shell.run_cell(cell_input)
    return km_run_cell(cell_input, user_variables=user_variables)

class CellQuestion(traits.HasTraits):

    metadata = traits.Dict
    answer = traits.Unicode
    correct_answer = traits.Unicode
    cell_input = traits.Unicode
    form = traits.Unicode
    identifier = traits.Unicode
    seed = traits.Int
    number = traits.Int
    shell = traits.Any(None)
    md5 = traits.Unicode
    user_id = traits.Unicode

    # the different outputs

    cell_outputs = traits.List
    form_outputs = traits.List
    comment_outputs = traits.List

    comments = traits.Dict({True:"<h2> Good job. Points: %(points)d / %(max_points)d </h2>",
                            False:"<h2> Try again. Points: %(points)d / %(max_points)d</h2>"})

    practice_comments = traits.Dict({True:"<h2> Good job. Here's another. Points: %(points)d / %(max_points)d </h2>",
                            False:"<h2> Try again. Here's another. Points: %(points)d / %(max_points)d</h2>"})

    points = traits.Dict({True:1,
                          False:0,
                          'max':1})

    practice = traits.Bool(False)

    def __init__(self, **kw):
        traits.HasTraits.__init__(self, **kw)
        self.on_trait_change(self.update_seed, ['seed'])
        self.on_trait_change(self.set_md5, ['cell_input', 'identifier', 'user_id'])
        self.on_trait_change(self.generate_cell_outputs, ['seed'])
        self.timestamp = datetime.datetime(*time.localtime()[:6])
        question_instances[(self.identifier, self.user_id)] = self

    def _shell_changed(self):
        run_cell('\n'.join(['%load_ext rmagic',
                            'from IPython.core.displaypub import publish_display_data',
                            'import numpy as np, random, json']),
                 shell=self.shell)

    def set_md5(self):
        h = md5()
        seed = self.retrieve_seed()
        h.update(self.cell_input + self.identifier + str(seed))
        self.md5 = h.hexdigest()

    def validate_md5(self, md5_hash):
        h = md5()
        seed = self.retrieve_seed()
        h.update(self.cell_input + self.identifier + str(seed))
        correct_md5_hash = h.hexdigest()
        return md5_hash == correct_md5_hash

    def update_seed(self):
        cell_input = '\n'.join(['seed=%d' % self.seed,
                                'np.random.seed(seed); random.seed(seed)',
                                '%R -i seed set.seed(seed); rm(seed)', ''])
        run_cell(cell_input, shell=self.shell)

    def generate_cell_outputs(self):
        self.cell_outputs, variables = run_cell(self.cell_input, 
                                                user_variables=['correct_answer'],
                                                shell=self.shell)[:2]
        self.correct_answer = eval(variables['correct_answer'])


    def form_cell(self, seed, shell=None):
        self.seed = seed; self.update_seed()
        cell = nbformat.new_code_cell(input=self.cell_input, 
                                      outputs=self.cell_outputs +
                                      self.form_outputs + self.comment_outputs)
        self.set_md5()
        cell.metadata['md5'] = self.md5
        self.metadata.update(cell.metadata)
        return cell
            
    def validate_answer(self):
        if self.answer:
            correct = self.answer == self.correct_answer
            if not self.practice:
                self.metadata['points'] = self.points[correct]
                self.metadata['max_points'] = self.points['max']
            else:
                self.metadata.setdefault('points', 0)
                self.metadata.setdefault('max_points', 0)
                self.metadata['points'] += self.points[correct]
                self.metadata['max_points'] += self.points['max']
            self.metadata['correct'] = correct # probably not necessary

    def retrieve_seed(self):
        return json.load(open(os.path.join(PATH_TO_HW_FILES,
                                           self.user_id, 
                                           "student_info.json"), 'rb'))['seed']


    def check_answer(self, cell_dict):
        cell = nbformat.NotebookNode(**cell_dict)
        self.metadata.update(cell.metadata)

        seed = self.retrieve_seed()

        self.set_md5()
        cell.metadata['md5'] = self.md5
        self.metadata.update(cell.metadata)
        import sys; sys.stderr.write('\nwriting md5 %s\n' % `(self.md5, cell.metadata['md5'])`)

        cell.metadata.setdefault('trial_number', 0)
        self.metadata.update(cell.metadata)
        seed += cell.metadata['trial_number']

        self.seed = seed; self.update_seed()

        # append the answer to the answer history

        cell.metadata.setdefault('answer_history', [])
        cell.metadata['answer_history'].append(cell.metadata['answer'])
        self.metadata.update(cell.metadata)

        # reset the outputs -- this should only trigger
        # generate_form_outputs and generate_comment_outputs but not
        # generate_cell_outputs because the seed should not have changed

        self.answer = cell.metadata['answer']
        cell.outputs = self.cell_outputs + self.form_outputs + self.comment_outputs
        cell.metadata.update(self.metadata)

        # if practice, regenerate the cell and its outputs

        if self.practice:
            cell['metadata']['trial_number'] += 1
            self.metadata.update(cell.metadata)
            seed += 1
            self.seed = seed # ; self.update_seed() # this last update_seed 
            # this should trigger regeneration of all 3 generate_*_outputs
            cell.outputs = self.cell_outputs + self.form_outputs + self.comment_outputs
            cell.metadata.update(self.metadata)

        return cell

    def generate_form_outputs(self):
        sys.stderr.write('\nform outputs\n')
        self.form_outputs = run_cell(self.form,
                                     shell=self.shell)[0]
        
    def generate_comment_outputs(self):
        self.validate_answer()
        correct = self.metadata['correct']
        sys.stderr.write('\ncomment outputs %s %s \n' % (`correct`, `self.metadata['correct']`))
        if not self.practice: 
            outputs = html_outputs(self.shell, self.comments[correct] % self.metadata)
        else:
            outputs = html_outputs(self.shell, self.practice_comments[correct] % self.metadata)
        self.comment_outputs = outputs


class MultipleChoiceCell(CellQuestion):

    choices = traits.List

    def __init__(self, **kw):
        CellQuestion.__init__(self, **kw)
        self.on_trait_change(self.generate_cell_outputs, ['seed'])
        self.on_trait_change(self.generate_form_input, ['answer', 
                                                        'choices',
                                                        'identifier',
                                                        'correct_answer'])
        self.on_trait_change(self.generate_form_outputs, ['form'])
        self.on_trait_change(self.generate_comment_outputs, ['answer'])

    def generate_cell_outputs(self):
        sys.stderr.write('\ncell outputs: %d %s\n' % (self.seed, `self.metadata`))
        # store the correct answer for checking later
        self.cell_outputs, variables = \
            run_cell(self.cell_input, 
                     user_variables=['correct_answer',
                                     'choices'], 
                     shell=self.shell)[:2]

        self.choices = eval(variables['choices'])
        self.correct_answer = eval(variables['correct_answer'])
        self.answer = ''

    def generate_form_input(self):
        sys.stderr.write('\nform inputs\n')
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
        self.set_md5()
        cell.metadata['md5'] = self.md5
        self.metadata.update(cell.metadata)
        return cell

    def check_answer(self, cell_dict, user):
        cell = nbformat.NotebookNode(**cell_dict)
        return cell

class TextBox(MultipleChoiceCell):

    correct_answer = traits.Any

    def __init__(self, **kw):
        CellQuestion.__init__(self, **kw)
        self.on_trait_change(self.generate_cell_outputs, ['seed'])
        self.on_trait_change(self.generate_form_input, ['answer', 
                                                        'identifier',
                                                        'correct_answer'])
        self.on_trait_change(self.generate_form_outputs, ['form'])
        self.on_trait_change(self.generate_comment_outputs, ['answer'])
        self.generate_form_input()

    def generate_cell_outputs(self):
        sys.stderr.write('\ncell outputs: %d %s\n' % (self.seed, `self.metadata`))
        # store the correct answer for checking later
        self.cell_outputs, variables = \
            run_cell(self.cell_input, 
                     user_variables=['correct_answer'], 
                     shell=self.shell)[:2]

        self.correct_answer = eval(variables['correct_answer'])
        self.answer = ''

    def generate_form_input(self):
        if self.answer:
            value = self.answer
        else:
            value = ''

        d = {'identifier': self.identifier, 'value':value }

        textbox_code = """<p><input type="text" name="%(identifier)s" value="%(value)s"> %(value)s</p>""" % d

        textbox_code = ('<form name="%(identifier)s" method="post" >\n' % d) + textbox_code + '</form>\n'
        form_input = '\n'.join(["publish_display_data('CellQuestion', {'text/latex':question_text})",
                                "publish_display_data('CellQuestion', {'text/html':'''%s'''})" % textbox_code]) 
        self.form = form_input

    def validate_answer(self):
        if self.answer:
            correct = np.allclose(self.answer, self.correct_answer)
            if not self.practice:
                self.metadata['points'] = self.points[correct]
                self.metadata['max_points'] = self.points['max']
            else:
                self.metadata.setdefault('points', 0)
                self.metadata.setdefault('max_points', 0)
                self.metadata['points'] += self.points[correct]
                self.metadata['max_points'] += self.points['max']
            self.metadata['correct'] = correct # probably not necessary


def html_outputs(shell, *raw_html_bits):
    return run_cell('\n'.join(["""publish_display_data("CellQuestion", {"text/html":'''%s'''})""" % raw_html for raw_html in raw_html_bits]), shell=shell)[0]

def latex_outputs(shell, *raw_latex_bits):
    return run_cell('\n'.join(["""publish_display_data("CellQuestion", {"text/latex":r'''%s'''})""" % raw_latex for raw_latex in raw_latex_bits]), shell=shell)[0]

