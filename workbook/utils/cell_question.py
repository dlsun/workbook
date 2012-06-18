import json
from workbook.io import *

import IPython.nbformat.current as nbformat
from workbook.utils.execute_and_save import shell, run_cell as km_run_cell

def run_cell(cell_input, shell=None):
    if shell is not None:
        shell.run_cell(cell_input)
    return km_run_cell(cell_input)

class CellQuestion(object):

    def __init__(self, cell_input, identifier):
        self.cell_input = cell_input
        self.identifier = identifier

    def set_seed(self, seed):
        cell_input = '\n'.join(['seed=%d' % seed,
                                '%load_ext rmagic',
                                'from IPython.core.displaypub import publish_display_data',
                                'import numpy as np, random, json',
                                'np.random.seed(seed); random.seed(seed)',
                                '%R -i seed set.seed(seed); rm(seed)', ''])
        return cell_input

    def set_answer(self, answer):
        cell_input = '\n'.join(['answer=%s' % json.dumps(answer), '']) 
        return cell_input

    def form_cell(self, seed, answer=None, shell=None):
        cell_input = self.set_seed(seed)
        if answer is not None:
            cell_input += self.set_answer(answer)
        cell_input += self.cell_input            
        outputs = run_cell(cell_input, shell=shell)

        cell = nbformat.new_code_cell(input=cell_input, outputs=outputs,
                                      metadata={})

        if answer is not None:
            answer_outputs = run_cell("\nanswer_metadata=check_answer(answer)\n")
            metadata_outputs = run_cell('\n'.join(["publish_display_data('CellQuestion', {'application/json':answer_metadata})", "del(answer_metadata)"]))
            outputs.append(answer_outputs)
            cell.metadata.update(metadata_outputs[0].json)
        return cell

    def check_answer(self, json_cell, user, answer, trial_number=0,
                     shell=None):
        """
        answer should be serializable through json, i.e.:
        answer = json.loads(json.dumps(answer))
        """
        seed = json.load(open(os.path.join(PATH_TO_HW_FILES,
                                           user['id'], 
                                           "student_info.json"), 'rb'))['seed']
        if hasattr(json_cell.metadata, "trial_number"):
            seed += json_cell.metadata.trial_number
        return self.form_cell(seed, answer, shell=shell)

class MultipleChoiceCell(CellQuestion):
    multiple_choice_check_answer = """
def check_answer(json_answer):
    answer = json_answer['answer']
    if answer not in choices:
        raise ValueError('answer should be on of the choices: %s' % `(answer, choices)`)
    correct = answer == correct_answer
    if correct:
        publish_display_data('CellQuestionOutput', {'text/html':'<h2>Good job!</h2>'})
    else:
        publish_display_data('CellQuestionOutput', {'text/html':'<h2>Try again!</h2>'})
    return {'correct':correct}
""" + '\n'

    def generate_form_input(self, choices, checked=None):
        form_input = ["publish_display_data('CellQuestion', {'text/latex':question_text})"]
                               
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
                                "publish_display_data('CellQuestion', {'text/html':'''%s'''})" % radio_code][:2]) 
        return form_input


    def form_cell(self, seed, answer=None, shell=None):
        cell_input = MultipleChoiceCell.multiple_choice_check_answer
        cell_input += self.set_seed(seed)
        if answer is not None:
            cell_input += self.set_answer(answer)
        cell_input += self.cell_input            
        outputs = run_cell(cell_input, shell=shell)

        cell = nbformat.new_code_cell(input=cell_input, outputs=outputs,
                                      metadata={})

        # get the choices and produce the buttons

        choice_outputs = run_cell("\npublish_display_data('CellQuestion', {'application/json':{'choices':choices}})\n", shell=shell)
        choices = choice_outputs[0].json['choices']
        form_outputs = run_cell(self.generate_form_input(choices, checked=answer), shell=shell)
        cell.outputs += form_outputs

        if answer is not None:
            answer_outputs = run_cell("\nanswer_metadata=check_answer(answer)\n", shell=shell)
            metadata_outputs = run_cell('\n'.join(["publish_display_data('CellQuestion', {'application/json':answer_metadata})", "del(answer_metadata)"]), shell=shell)
            outputs.append(answer_outputs)
            cell.metadata.update(metadata_outputs[0].json)
        return cell


