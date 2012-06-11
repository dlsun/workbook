import tempfile, os
import IPython.nbformat.current as nbformat

import encrypt, set_owner

def compose_converters(nb, *converter_classes):
    ofilename = tempfile.mkstemp()[1] + '.ipynb'
    nfilebase = tempfile.mkstemp()[1]
    with open(ofilename, 'wb') as ofile:
        nbformat.write(nb, ofile, 'json')
    for converter_class in converter_classes:
        converter = converter_class(ofilename, nfilebase)
        nfilename = converter.render()
        os.rename(nfilename, ofilename)
    nb = nbformat.read(file(ofilename, 'rb'), 'json')
    os.remove(ofilename)
    return nb

