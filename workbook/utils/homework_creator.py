"""
This module gives an example of inserting a worksheet into an 
existing notebook.
"""

import copy, os, sys, shutil, json
import glob
from .execute_and_save import execute_and_save
from ..external import nbconvert as nbc
from workbook.io import *

def merge_notebooks(outbase, *notebooks):
    if len(notebooks) == 0:
        raise ValueError('no notebooks to merge!')
    converter = nbc.ConverterNotebook(notebooks[0], outbase)
    converter.read()
    for notebook in notebooks[1:]:
        notebook_reader = nbc.Converter(notebook)
        notebook_reader.read()

        converter.nb.worksheets += notebook_reader.nb.worksheets
    return converter.render()

def create_assignment(assignmentfile, student_info):
    assignmentbase = os.path.splitext(assignmentfile)[0]
    student_info = json.load(file(student_info, 'rb'))
    student_id = student_info['id']

    # make output directory

    odir = os.path.join(PATH_TO_HW_FILES, student_id)
    if not os.path.exists(odir):
        os.makedirs(odir)

    outfile = os.path.join(odir, os.path.split(assignmentfile)[1])
    shutil.copy(assignmentfile, outfile)

    execute_and_save(outfile, student_info)



