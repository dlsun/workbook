from workbook.external import nbconvert as nbc

class MetadataSetter(nbc.ConverterNotebook):

    def __init__(self, infile, outbase, owner):
        self.owner = owner
        nbc.ConverterNotebook.__init__(self, infile, outbase)

    def preprocess(self, cell):
        if ('owner' not in cell.metadata and cell.cell_type == 'code'
            and cell.input):
            cell.metadata.update({'owner':'workbook',
                                  'group':self.owner})

