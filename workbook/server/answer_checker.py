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
        question_cp.seed = question_cp.retrieve_seed() # setting seed should trigger question to generate
        question_instances[tag] = question_cp

    return question_instances[tag]

def find_cell(input_cell, nb):
    for ws in nb.worksheets:
        for cell in ws.cells:
            if hasattr(cell, 'input') and hasattr(cell, 'metadata') and hasattr(cell.metadata, 'identifier') and\
                    cell.metadata['identifier']==input_cell.metadata['identifier']:
                return cell
    raise Exception


def check_answer(cell_dict, user, nb):

    global BUFFER_COUNTER
    BUFFER_COUNTER += 1; BUFFER_COUNTER = BUFFER_COUNTER % 500
    if BUFFER_COUNTER == 0:
        flush_buffer(question_instances)

    # find cell in notebook and use its metadata, except for answer
#    try:
    user_cell = nbformat.NotebookNode(**cell_dict)
    nb_cell = find_cell(user_cell, nb)
    nb_cell.metadata['answer'] = user_cell.metadata['answer']

    question = get_question(nb_cell, user)

    cell = question.check_answer(nb_cell)
    cell.cell_type = 'workbook'

 #   except Exception as e:
 #       import sys; sys.stderr.write('Error in Checking Answer: ' + str(e) + '\n')
 #       # just return cell to user without doing anything
 #       cell = nbformat.NotebookNode(**cell_dict)

    import sys; sys.stderr.write('Type: ' + cell.cell_type)
        
    return cell

def calculate_grade(nb):
    total_points = 0
    total_max_points = 0
    for ws in nb.worksheets:
        for cell in ws.cells:
            if hasattr(cell, 'metadata') and hasattr(cell['metadata'], 'points'):
                total_points += cell['metadata']['points']
                total_max_points += cell['metadata']['max_points']
    return total_points, total_max_points

