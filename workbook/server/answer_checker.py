# IPython shell to check answers

import os
from workbook.converters import ConverterNotebook

from workbook.utils.questions import (find_identified_cells,
                                      find_identified_outputs,
                                      update_output)

from IPython.lib.irunner import IPythonRunner
shell = IPythonRunner()

def check_answer(filename, identifier, answer):
    tmpf = os.path.splitext(filename)[0] + '_tmp'
    converter = ConverterNotebook(filename, tmpf)
    converter.read()

    cells = find_identified_cells(converter.nb, identifier)
    if len(cells) > 1:
        raise ValueError('more than one match: %s' % '\n'.join([str(c) for c in cells]))
    outputs = find_identified_outputs(cells[0], identifier)
    for output in outputs:
        update_output(output, identifier, answer)

    outfile = converter.render()
    os.rename(outfile, filename)
    return filename
