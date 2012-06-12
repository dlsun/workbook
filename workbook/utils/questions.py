import numpy as np
from IPython.core.displaypub import publish_display_data
import json

submitform = ""


submitform_js = """
function submit%(identifier)s()
{
  document.%(identifier)s.submit();
}
"""

class HomeworkCounter(object):

    def __init__(self):
        self.question_number = 1

    def next(self):
        publish_display_data("HomeworkBuilder", {'text/html':"<h2>Question %d</h2>" % self.question_number})
        self.question_number += 1


def multiple_choice(question_text, choices, correct_answer, identifier, assignment_num=1):
    """
    Generate a multiple choice question with given text and choices, and name the input form identifier
    """
    publish_display_data("HomeworkBuilder", {'text/latex':question_text})

    # shuffle the choices
    np.random.shuffle(choices)

    radio_code = ('<form name="multiple" method="post" action="%s/check">\n' % ('assignment%d' % assignment_num))  + '\n'.join(['''
    <p><input type="radio" name="%(name)s" value="%(value)s" id="%(value)s"> %(value)s</p>
    ''' % {'name':identifier, 'value':choice, 'id':d, 'url':'assignment%d' % assignment_num} for d, choice in enumerate(choices)]) + '</form>\n'

    radio_code += submitform % {'identifier':identifier}

    if correct_answer not in list(choices):
        raise ValueError('the correct answer should be one of the choices!')

    publish_display_data("HomeworkBuilder", {'text/html':radio_code})
    publish_display_data("HomeworkBuilder", {'application/json': {'question_identifier':identifier,
                                                                  'checkable':True,
                                                                  'correct_answer':correct_answer}})
    publish_display_data("HomeworkBuilder", {'application/javascript': submitform_js % {'identifier':identifier}})

def text_box(question_text, correct_answer, identifier, assignment_num=1):
    """
    Generate a text box answer question with given textname the input form identifier
    """
    publish_display_data("HomeworkBuilder", {'text/latex':question_text})
    textbox_code = '''
    <form method="post" action="%(url)s/check"><p><input type="text" name="%(name)s"></p></form>
    ''' % {'name':identifier,'url':'assignment%d' % assignment_num} 

    textbox_code += submitform % {'identifier':identifier}

    publish_display_data("HomeworkBuilder", {'text/html':textbox_code})
    publish_display_data("HomeworkBuilder", {'application/json': {'question_identifier':identifier,
                                                                  'checkable':False,
                                                                  'correct_answer':correct_answer}})
    publish_display_data("HomeworkBuilder", {'application/javascript': submitform_js % {'identifier':identifier}})

def true_false(question_text, correct_answer, identifier, assignment_num=1):
    """
    Generate a true or false question with given textname the input form identifier
    """
    publish_display_data("HomeworkBuilder", {'text/latex':"(True/False) " + question_text})


    choices = ['True', 'False']
    radio_code = '<form method="post" action="%(url)s/check">\n' + '\n'.join(['''
    <p><input type="radio" name="%(name)s" value="%(value)s" id="%(value)s"> %(value)s</p>
    ''' % {'name':identifier, 'value':choice, 'url':'assignment%d' % assignment_num} for choice in choices]) + '</form>\n' 

    radio_code += submitform % {'identifier':identifier}
    if correct_answer not in [True, False]:
        raise ValueError('the correct answer should be one of [True, False]')
    publish_display_data("HomeworkBuilder", {'text/html':radio_code})
    publish_display_data("HomeworkBuilder", {'application/json': {'question_identifier':identifier,
                                                                  'checkable':True,
                                                                  'correct_answer':correct_answer}})
    publish_display_data("HomeworkBuilder", {'application/javascript': submitform_js % {'identifier':identifier}})

def is_identified_cell(cell, identifier):
    if hasattr(cell, 'outputs'):
        for output in cell.outputs:
            if 'json' in output:
                try:
                    if 'question_identifier' in output.json.keys():
                        print 'question_identifier', output.json['question_identifier']
                        if output.json['question_identifier'] == identifier:
                            return True, output
                except AttributeError:
                    pass
    return False, None

def find_identified_cell(nb, identifier):
    for ws in nb.worksheets:
        for cell in ws.cells:
            check, value = is_identified_cell(cell, identifier)
            if check:
                return value
    return None

