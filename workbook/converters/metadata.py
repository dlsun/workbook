import json

from workbook.external import nbconvert as nbc
import base64

from IPython.nbformat.current import NotebookNode

class set_group(nbc.ConverterNotebook):

    def __init__(self, infile, outbase, owner):
        self.owner = owner
        nbc.ConverterNotebook.__init__(self, infile, outbase)

    # for now, the javascript only knows code cells as workbook cells
        
    def preprocess(self, cell):
        if ('owner' not in cell.metadata and cell.cell_type == 'code'
            and cell.input):
            cell.metadata.update({'owner':'workbook',
                                  'group':self.owner})
            

