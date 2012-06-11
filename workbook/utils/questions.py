import numpy as np
from IPython.core.displaypub import publish_display_data
import json

def question(number):
    publish_display_data("HomeworkBuilder", {'text/html':"<h2>Question 2</h2>"})

def multiple_choice(question_text, choices, correct_answer, identifier):
    """
    Generate a multiple choice question with given text and choices, and name the input form identifier
    """
    publish_display_data("HomeworkBuilder", {'text/latex':question_text})

    # shuffle the choices
    np.random.shuffle(choices)

    radio_code = '\n'.join(['''
    <p><input type="radio" name="%(name)s" value="%(value)s"> %(value)s</p>
    ''' % {'name':identifier, 'value':choice} for choice in choices])

    if correct_answer not in list(choices):
        raise ValueError('the correct answer should be one of the choices!')

    publish_display_data("HomeworkBuilder", {'text/html':radio_code})
    publish_display_data("HomeworkBuilder", {'application/json': {'question_identifier':identifier,
                                                                  'checkable':True,
                                                                  'correct_answer':correct_answer}})


def text_box(question_text, correct_answer, identifier):
    """
    Generate a text box answer question with given textname the input form identifier
    """
    publish_display_data("HomeworkBuilder", {'text/latex':question_text})
    textbox_code = '''
    <p><input type="text" name="%(name)s"></p>
    ''' % {'name':identifier} 

    publish_display_data("HomeworkBuilder", {'text/html':textbox_code})
    publish_display_data("HomeworkBuilder", {'application/json': {'question_identifier':identifier,
                                                                  'checkable':False,
                                                                  'correct_answer':correct_answer}})

def true_or_false(question_text, correct_answer, identifier):
    """
    Generate a true or false question with given textname the input form identifier
    """
    publish_display_data("HomeworkBuilder", {'text/latex':"(True/False) " + question_text})

    choices = ['True', 'False']
    radio_code = '\n'.join(['''
    <p><input type="radio" name="%(name)s" value="%(value)s"> %(value)s</p>
    ''' % {'name':identifier, 'value':choice} for choice in choices])

    if correct_answer not in [True, False]:
        raise ValueError('the correct answer should be one of [True, False]')
    publish_display_data("HomeworkBuilder", {'text/html':radio_code})
    publish_display_data("HomeworkBuilder", {'application/json': {'question_identifier':identifier,
                                                                  'checkable':True,
                                                                  'correct_answer':correct_answer}})

