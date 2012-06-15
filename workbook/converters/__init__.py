import tempfile, os
import IPython.nbformat.current as nbformat

from metadata import AddMetadata

from ..external.nbconvert import ConverterNotebook, Converter

import encrypt, owner

def compose_converters(nb, *converter_instances):
    ofilename = tempfile.mkstemp()[1] + '.ipynb'
    nfilebase = tempfile.mkstemp()[1]
    with open(ofilename, 'wb') as ofile:
        nbformat.write(nb, ofile, 'json')
    for converter in converter_instances:
        converter.infile = ofilename
        converter.read()
        converter.output = converter.convert()
        # ofilename should be nfilename... so last line should be reduntant
        nfilename = converter.save(outfile=ofilename)
        os.rename(nfilename, ofilename)
    sync_metadata_name(ofilename)
    nb = nbformat.read(file(ofilename, 'rb'), 'json')
    os.remove(ofilename)
    return nb

def sync_metadata_name(nbfilename):

    nb = nbformat.read(open(nbfilename, 'rb'), 'json')
    nb.metadata.name = os.path.splitext(os.path.split(nbfilename)[1])[0]
    nbformat.write(nb, open(nbfilename, 'wb'), 'json')
