"""
This module gives an example of inserting a worksheet into an 
existing notebook.
"""

import copy, os, sys, shutil
import glob
from .execute_and_save import execute_and_save
from ..converters import owner, encrypt, sync_metadata_name
from ..external import nbconvert as nb

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
    sync_metadata_name(outfile)
    return outfile


def main():
    dd = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    print dd, 'path'
    def p(*n): return os.path.join(dd, *n)
                        
    create_assignment(p('assignment1'), p('headers','standard_header.ipynb'), p('students','leland_stanford.ipynb'))

if __name__ == "__main__":
    main()

