import json

from ..external import nbconvert as nbc
import base64

from IPython.nbformat.current import NotebookNode

def find_metadata(cell):
    results = []
    if hasattr(cell, 'outputs'):
        for output in cell.outputs:
            if 'json' in output:
                try:
                    if 'workbook_metadata' in output.json.keys():
                        results.append(output)
                except:
                    pass
    if results:
        return results[-1] # the last one -- but we really should 
                           # collect it all

class AddMetadata(nbc.ConverterNotebook):
    """
    Add a dictionary of metadata to each cell.
    """

    def __init__(self, infile, outbase, metadata):
        nbc.ConverterNotebook.__init__(self, infile, outbase)
        self.metadata = metadata
        self.output = NotebookNode(output_type='display_data')
        self.output.json = metadata

    def render_code(self, cell):
        """Convert a code cell

        Returns list."""
        output = find_metadata(cell)
        if output is None:
            cell.outputs.append(self.output)
        else:
            for key, value in self.metadata.items():
                output.json['workbook_metadata'][key] = value
        return nbc.ConverterNotebook.render_code(self, cell)


class StudentMetadata(nbc.ConverterNotebook):
    extension = 'json' # the output is not officially .ipynb
    default_output = NotebookNode(output_type='display_data')
    default_output.json = {'workbook_metadata':{'owner':'student'}}

    def render_heading(self, cell):
        output = find_metadata(cell) or self.default_output
        metadata = output.json['workbook_metadata']
        for key, value in metadata.items():
            setattr(cell, key, value)
        return nbc.ConverterNotebook.render_heading(self, cell)

    def render_code(self, cell):
        output = find_metadata(cell) or self.default_output
        metadata = output.json['workbook_metadata']
        for key, value in metadata.items():
            setattr(cell, key, value)
        return nbc.ConverterNotebook.render_code(self, cell)

    def render_markdown(self, cell):
        output = find_metadata(cell) or self.default_output
        metadata = output.json['workbook_metadata']
        for key, value in metadata.items():
            setattr(cell, key, value)
        return nbc.ConverterNotebook.render_markdown(self, cell)

    def render_raw(self, cell):
        output = find_metadata(cell) or self.default_output
        metadata = output.json['workbook_metadata']
        for key, value in metadata.items():
            setattr(cell, key, value)
        return nbc.ConverterNotebook.render_raw(self, cell)

class TAMetadata(StudentMetadata):
    default_output = NotebookNode(output_type='display_data')
    default_output.json = {'workbook_metadata':{'owner':'TA'}}

class RemoveMetadata(nbc.ConverterNotebook):

    def render_heading(self, cell):
        output = find_metadata(cell)
        if output:
            metadata = output.json['workbook_metadata']
            for key in metadata.keys():
                try:
                    delattr(cell, key)
                except AttributeError:
                    pass
        return nbc.ConverterNotebook.render_heading(self, cell)

    def render_code(self, cell):
        output = find_metadata(cell)
        if output: 
            metadata = output.json['workbook_metadata']
            for key in metadata.keys():
                try:
                    delattr(cell, key)
                except AttributeError:
                    pass
        return nbc.ConverterNotebook.render_code(self, cell)

    def render_markdown(self, cell):
        output = find_metadata(cell)
        if output:
            metadata = output.json['workbook_metadata']
            for key in metadata.keys():
                try:
                    delattr(cell, key)
                except AttributeError:
                    pass
        return nbc.ConverterNotebook.render_markdown(self, cell)

    def render_raw(self, cell):
        output = find_metadata(cell)
        if output: 
            metadata = output.json['workbook_metadata']
            for key in metadata.keys():
                try:
                    delattr(cell, key)
                except AttributeError:
                    pass
        return nbc.ConverterNotebook.render_raw(self, cell)

if __name__ == "__main__":

    student = StudentMetadata('../../notebooks/leland_stanford/Assignment1.ipynb', 'student')
    student.render()
    ta = TAMetadata('../../notebooks/leland_stanford/Assignment1.ipynb', 'ta')
    ta.render()
