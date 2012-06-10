"""
This module gives an example of inserting a worksheet into an 
existing notebook.
"""

import copy, os, sys
import glob

sys.path.append('/Users/jonathantaylor/nbconvert') # to find nbconvert
import nbconvert as nb
from execute_and_save import execute_and_save

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

def create_assignment(assignmentdir, header, student_nb):
    outdir = os.path.join('output', assignmentdir)
    if not os.path.exists(outdir):
        os.makedirs(outdir)
    student_id = os.path.splitext(os.path.split(student_nb)[1])[0]
    questions = sorted(glob.glob(os.path.join(assignmentdir, 'q*.ipynb')))
    outfile = merge_notebooks(os.path.join(outdir, student_id), student_nb, header, *questions)
    return outfile

def dump_display_html(nbfile):

    converter = ConverterQuickHTML(nbfile)
    converter.render()


def dump_display_latex(nbfile):

    converter = ConverterLaTeX(nbfile)
    converter.render()

class ConverterQuickHTML(nb.ConverterQuickHTML):

    def render_code(self, cell):
        # returns only display_data of cell
        lines = ['<table>']
        cell = nb.split_lines_cell(copy.deepcopy(cell))
        for output in cell.outputs:
            if output.output_type == 'display_data':
                lines.append('<tr><td></td><td>')
                conv_fn = self.dispatch(output.output_type)
                lines.extend(conv_fn(output))
                lines.append('</td></tr>')
        
        lines.append('</table>')
        return lines

class ConverterLaTeX(nb.ConverterLaTeX):

    def render_code(self, cell):
        # returns only display_data of cell

        lines = []
        outlines = []
        for output in cell.outputs:
            if output.output_type == 'display_data':
                conv_fn = self.dispatch(output.output_type)
                outlines.extend(conv_fn(output))

        # And then output of many possible types; use a frame for all of it.
        if outlines:
            lines.extend(self.in_env('codeoutput', outlines))

        return lines


if __name__ == '__main__':
    import shutil
    outdir = '../hw_templates'
    assignment1 = 'assignment1.ipynb'
    create_assignment('assignment1', 'headers/standard_header.ipynb', 'students/leland_stanford.ipynb')
    execute_and_save('output/assignment1/leland_stanford.ipynb')
    shutil.copy('output/assignment1/leland_stanford_executed.ipynb',
                '%s/leland_stanford.ipynb' % outdir)
    
