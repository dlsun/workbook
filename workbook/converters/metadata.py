import json

from ..external import nbconvert as nbc
import base64

from IPython.nbformat.current import NotebookNode

def find_metadata(cell):
    if hasattr(cell, 'outputs'):
        for output in cell.outputs:
            if 'json' in output:
                try:
                    if 'workbook_metadata' in output.json.keys():
                        return output.json['workbook_metadata']
                except:
                    pass
    return {'owner':'noone'}

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
        cell.outputs.append(self.output)
        return nbc.ConverterNotebook.render_code(self, cell)


class StudentMetadata(nbc.ConverterNotebook):
    extension = 'json' # the output is not officially .ipynb
    default_metadata = {'owner':'student'}

    def render_heading(self, cell):
        metadata = find_metadata(cell) or self.default_metadata
        for key, value in metadata.items():
            setattr(cell, key, value)
        return nbc.ConverterNotebook.render_heading(self, cell)

    def render_code(self, cell):
        metadata = find_metadata(cell) or self.default_metadata
        for key, value in metadata.items():
            setattr(cell, key, value)
        return nbc.ConverterNotebook.render_code(self, cell)

    def render_markdown(self, cell):
        metadata = find_metadata(cell) or self.default_metadata
        for key, value in metadata.items():
            setattr(cell, key, value)
        return nbc.ConverterNotebook.render_markdown(self, cell)

    def render_raw(self, cell):
        metadata = find_metadata(cell) or self.default_metadata
        for key, value in metadata.items():
            setattr(cell, key, value)
        return nbc.ConverterNotebook.render_raw(self, cell)

class TAMetadata(StudentMetadata):
    default_metadata = {'owner':'TA'}

class RemoveMetadata(nbc.ConverterNotebook):

    def render_heading(self, cell):
        metadata = find_metadata(cell) or self.default_metadata
        for key in metadata.keys():
            try:
                delattr(cell, key)
            except AttributeError:
                pass
        return nbc.ConverterNotebook.render_heading(self, cell)

    def render_code(self, cell):
        metadata = find_metadata(cell) or self.default_metadata
        for key in metadata.keys():
            try:
                delattr(cell, key)
            except AttributeError:
                pass
        return nbc.ConverterNotebook.render_code(self, cell)

    def render_markdown(self, cell):
        metadata = find_metadata(cell) or self.default_metadata
        for key in metadata.keys():
            try:
                delattr(cell, key)
            except AttributeError:
                pass
        return nbc.ConverterNotebook.render_markdown(self, cell)

    def render_raw(self, cell):
        metadata = find_metadata(cell) or self.default_metadata
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

