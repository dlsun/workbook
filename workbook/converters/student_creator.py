import json, os
from ..external import nbconvert as nbc
import IPython.nbformat.current as nbformat
from numpy.random import randint

datadir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
PATH_TO_STUDENTS = os.path.join(datadir, 'students')

lsjfile = os.path.join(PATH_TO_STUDENTS, 'leland_stanford.ipynb')

class StudentCreator(nbc.ConverterNotebook):

    def __init__(self, sunet_id, student_name=None):
        outbase = os.path.join(PATH_TO_STUDENTS, sunet_id)
        nbc.ConverterNotebook.__init__(self, lsjfile, outbase)
        self.sunet_id = sunet_id
        self.student_name = student_name

    # there is only one code cell
    def render_code(self, cell):
        cell.input = cell.input.replace('LSJ', self.sunet_id)
        student_name = self.student_name or self.sunet_id
        cell.input = cell.input.replace('Stanford, Leland', student_name)
        seed = randint(low=0,high=10**7)
        cell.input = cell.input.replace('1891', str(seed))
        return nbc.ConverterNotebook.render_code(self, cell)

if __name__ == "__main__":

    student = StudentCreator('jonathan.taylor')
    ofile = student.render()
    print ofile

