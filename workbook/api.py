import numpy as np, random

from IPython.core.displaypub import publish_display_data

class HomeworkCounter(object):

    def __init__(self):
        self.question_number = 0

    def next(self):
        self.question_number += 1
        publish_display_data("HomeworkBuilder", {'text/html':"<h2>Question %d</h2>" % self.question_number})

counter = HomeworkCounter()

import workbook.utils.magics 


