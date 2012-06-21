# IPython shell to check answers

from copy import copy
import os
from workbook.converters import ConverterNotebook
import IPython.nbformat.current as nbformat
from workbook.utils.cell_question import question_types, question_instances
from workbook.io import *


BUFFER_SIZE = 500 # keep 500 question instances around at any onetime
BUFFER_COUNTER = 0
def flush_buffer(question_instances):
    if len(question_instances) < BUFFER_SIZE:
        return
    else:
        oldest_timestamps = sorted([(q.timestamp, k) for k, q in question_instances.items()])[::-1][BUFFER_SIZE:]
        for _, k in oldest_timestamps:
            del(question_instances[k])

def get_question(cell, user):
    try:
        tag = (cell.metadata['identifier'], user['id'])
    except (KeyError, AttributeError):
        return None

    if tag not in question_instances:
        # generate the question on the fly
        question_cp = copy(question_types[cell.metadata['identifier']])
        question_cp.user_id = user['id']
        question_cp.metadata = cell.metadata
        question_cp.seed = question_cp.retrieve_seed()
        question_instances[tag] = question_cp

    return question_instances[tag]

def check_answer(cell_dict, user):

    global BUFFER_COUNTER
    BUFFER_COUNTER += 1; BUFFER_COUNTER = BUFFER_COUNTER % 50
    if BUFFER_COUNTER == 0:
        flush_buffer(question_instances)

    cell = nbformat.NotebookNode(**cell_dict)
    question = get_question(cell, user)

    if question is not None:
        cell = question.check_answer(cell_dict)
        cell.input = user['cipher'].encrypt(cell.input)
        cell.metadata['input_encrypted'] = True
        cell.cell_type = 'workbook'

    return cell

def get_grades(cell_dict, user):
    if type(cell_dict) == type({}):
        cell = nbformat.NotebookNode(**cell_dict)
    else:
        cell = cell_dict
    question = get_question(cell, user)

    if question is not None:
        cell.input = user['cipher'].encrypt(cell.input)
        cell.metadata['input_encrypted'] = True
        cell.cell_type = 'workbook'

        if 'md5' in cell.metadata and question.validate_md5(cell.metadata['md5']):
            return ((question.number, question.metadata['points'], question.metadata['max_points']), cell)
    return ((None, None, None), cell)
