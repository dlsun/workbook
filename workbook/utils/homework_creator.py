"""
This module gives an example of inserting a worksheet into an 
existing notebook.
"""

import copy, os, sys, shutil, json
import glob
from .execute_and_save import execute_and_save
from ..converters import encrypt, sync_metadata_name, AddMetadata
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

    # inject the seed as the first line of the first code cell
    # should be a neater way to do this
    nb = nbc.nbformat.read(open(outfile, 'rb'), 'json')
    # it doesn't seem like inserted_seed is doing anything -Dennis
    inserted_seed = False
    for ws in nb.worksheets:
        if not inserted_seed:
            for cell in ws.cells:
                if cell.cell_type == 'code':
                    cell.input = 'seed=%d\n' % student_info['seed'] + cell.input
                    inserted_seed = True
                    break

    nbc.nbformat.write(nb, open(outfile, 'wb'), 'json')
    newfile = execute_and_save(outfile)
    os.rename(newfile, outfile)
    converter = AddMetadata(outfile, os.path.splitext(outfile)[0] + '_tmp',
                            {'owner':'workbook',
                             'user':'teacher'})
    newfile = converter.render()
    os.rename(newfile, outfile)

    # do we really need this metadata? -Dennis
    sync_metadata_name(outfile)

    return outfile



