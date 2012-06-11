"""
This module gives an example of inserting a worksheet into an 
existing notebook.
"""

import copy, os, sys, shutil
import glob
from execute_and_save import execute_and_save
from converters import set_owner, encrypt

sys.path.append('/Users/jonathantaylor/nbconvert') # to find nbconvert
import nbconvert as nb

def merge_notebooks(outbase, *notebooks):
    if len(notebooks) == 0:
        raise ValueError('no notebooks to merge!')
    converter = nb.ConverterNotebook(notebooks[0], outbase)
    converter.read()
    for notebook in notebooks[1:]:
        notebook_reader = nb.Converter(notebook)
        notebook_reader.read()

        converter.nb.worksheets += notebook_reader.nb.worksheets
    return converter.render()

def create_assignment(assignmentbase, header, student_nb):
    student_id = os.path.splitext(os.path.split(student_nb)[1])[0]
    odir = os.path.join('..', 'notebooks', student_id)
    if not os.path.exists(odir):
        os.makedirs(odir)
    questions = sorted(glob.glob(os.path.join(assignmentbase, 'q*.ipynb')))
    outfile = merge_notebooks(os.path.join(odir, os.path.split(assignmentbase)[1]), student_nb, header, *questions)
    newfile = execute_and_save(outfile)
    os.rename(newfile, outfile)
    return outfile

if __name__ == "__main__":

    create_assignment('../assignment1', '../headers/standard_header.ipynb', '../students/leland_stanford.ipynb')
