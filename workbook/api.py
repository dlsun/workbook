import numpy as np, random

def set_seed(seed=0):

    random.seed(seed)
    np.random.seed(seed)

    # set the seed in R

    ip = get_ipython()
    ip.user_ns['seed'] = seed
    ip.magic('R -i seed set.seed(seed)')


from .utils.questions import *
from IPython.core.displaypub import publish_display_data
counter = HomeworkCounter()

import workbook.utils.homework_magics

