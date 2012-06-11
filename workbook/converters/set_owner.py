import json
import sys
sys.path.append('/Users/jonathantaylor/nbconvert')

import nbconvert as nbc
import base64

def find_owner(cell):
    for output in cell.outputs:
        if 'json' in output:
            try:
                if 'owner' in output.json.keys():
                    return output.json['owner']
            except:
                pass
    return None

class StudentOwner(nbc.ConverterNotebook):
    extension = 'json' # the output is not officially .ipynb
    default_owner = 'student'

    def render_heading(self, cell):
        owner = find_owner(cell)
        if cell.input:
            cell.owner = owner or self.default_owner
        else:
            cell.owner = self.default_owner
        return nbc.ConverterNotebook.render_heading(self, cell)

    def render_code(self, cell):
        owner = find_owner(cell) or self.default_owner
        if cell.input:
            cell.owner = owner or self.default_owner
        else:
            cell.owner = self.default_owner
        return nbc.ConverterNotebook.render_code(self, cell)

    def render_markdown(self, cell):
        owner = find_owner(cell) or self.default_owner
        if cell.input:
            cell.owner = owner or self.default_owner
        else:
            cell.owner = self.default_owner
        return nbc.ConverterNotebook.render_markdown(self, cell)

    def render_raw(self, cell):
        owner = find_owner(cell) or self.default_owner
        if cell.input:
            cell.owner = owner or self.default_owner
        else:
            cell.owner = self.default_owner
        return nbc.ConverterNotebook.render_raw(self, cell)

class TAOwner(StudentOwner):
    default_owner = 'TA'

class RemoveOwner(nbc.ConverterNotebook):

    def render_heading(self, cell):
        if "owner" in cell.keys():
            del(cell.owner)
        return nbc.ConverterNotebook.render_heading(self, cell)

    def render_code(self, cell):
        if "owner" in cell.keys():
            del(cell.owner)
        return nbc.ConverterNotebook.render_code(self, cell)

    def render_markdown(self, cell):
        if "owner" in cell.keys():
            del(cell.owner)
        return nbc.ConverterNotebook.render_markdown(self, cell)

    def render_raw(self, cell):
        if "owner" in cell.keys():
            del(cell.owner)
        return nbc.ConverterNotebook.render_raw(self, cell)

if __name__ == "__main__":

    student = StudentOwner('../notebooks/leland_stanford/Assignment1.ipynb', 'student')
    student.render()
    ta = TAOwner('../notebooks/leland_stanford/Assignment1.ipynb', 'ta')
    ta.render()

