import json
from workbook.utils.questions import Question
from workbook.io import *

from workbook.utils.execute_and_save import shell, run_cell

class CellQuestion(Question):

    def __init__(self, cell):
        self.cell = cell
        shell.execute('%load_ext rmagic')

    def check_answer(self, answer, trial, user_id):
        """
        answer should be serializable through json, i.e.:
        answer = json.loads(json.dumps(answer))
        """
        seed = json.load(open(os.path.join(PATH_TO_HW_FILES,
                                           user_id, 
                                           "student_info.json"), 'rb'))['seed']
        cell = ('\n'.join(['seed=%d' % seed,
                'import numpy as np, random, json',
                'np.random.seed(seed); random.seed(seed)',
                '%R -i seed set.seed(seed); rm(seed)',
                 'answer=json.loads("""%s""")' % json.dumps(answer)]) +
                self.cell)
        outputs = run_cell(cell)
        return run_cell("check_answer(answer)")

    @property
    def constructor_info(self):
        return None

    def set_answer(self):
        raise NotImplementedError

    def get_answer(self):
        raise NotImplementedError

    answer = property(get_answer, set_answer)



