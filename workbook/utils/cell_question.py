import json
from workbook.utils.questions import Question
from workbook.io import *

from workbook.utils.execute_and_save import shell, run_cell

class CellQuestion(Question):

    def __init__(self, cell_input, identifier):
        self.cell_input = cell_input
        self.identifier = identifier

    def set_seed(self, seed):
        cell_input = '\n'.join(['seed=%d' % seed,
                                'import numpy as np, random',
                                'np.random.seed(seed); random.seed(seed)',
                                '%R -i seed set.seed(seed); rm(seed)'])
        run_cell(cell_input)
        return cell_input

    def set_answer(self, answer):
        cell_input = '\n'.join(['import json',
                                'answer=json.loads("""%s""")' % json.dumps(answer)]) +
        run_cell(cell_input)
        return cell_input

    def run_cell(self):
        run_cell(self.cell_input)

    def check_answer(self, json_cell, user, answer, trial_number=0,
                     shell=None):
        """
        answer should be serializable through json, i.e.:
        answer = json.loads(json.dumps(answer))
        """
        filename = os.path.join(PATH_TO_HW_FILES, user['id'], nbname + '.ipynb')
        seed = json.load(open(os.path.join(PATH_TO_HW_FILES,
                                           user_id, 
                                           "student_info.json"), 'rb'))['seed']
        if hasattr(json_cell.metadata, trial_number):
            seed += json_cell.metadata.trial_number

        cell_input = ''
        cell_input += self.set_seed(seed)
        cell_input += self.set_answer(answer)
        cell_input += self.cell_input
        outputs = self.run_cell()
        outputs.append(run_cell("check_answer(answer)"))
        return new_code_cell(input=cell_input, outputs=outputs,
                             metadata={})

    @property
    def constructor_info(self):
        return None

    def set_answer(self):
        raise NotImplementedError

    def get_answer(self):
        raise NotImplementedError

    answer = property(get_answer, set_answer)



