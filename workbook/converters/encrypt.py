import json

from ..external import nbconvert as nbc
import base64

# pycrypto tools

from Crypto.Cipher import AES
BLOCK_SIZE = 16
KEY_SIZE = 16
AES.block_size = BLOCK_SIZE

from metadata import find_and_merge_metadata

class Cipher(object):
    
    def __init__(self, key, iv):
        self.cipher = AES.new(key, AES.MODE_CFB, iv)
        self.block_size = AES.block_size

    def encrypt(self, msg):
        # pad with "[" as an unlikely end character as we are encrypting json
        # http://www.codekoala.com/blog/2009/aes-encryption-python-using-pycrypto/
        padded_msg = ']'*self.block_size + msg + (AES.block_size - len(msg) % AES.block_size) * '['
        return base64.b64encode(self.cipher.encrypt(padded_msg))

    def decrypt(self, msg):
        decrypted_msg = self.cipher.decrypt(base64.b64decode(msg)).rstrip('[')
        return decrypted_msg[self.block_size:]

key = b'Sixteen byte key'
iv = 's\xa7\xdcXx\xab\rn\x18\x84\x9a\x15\x12lC-'

bad_cipher = Cipher(key, iv)

class EncryptTeacherInfo(nbc.ConverterNotebook):

    def __init__(self, infile, outbase, cipher):
        self.cipher = cipher
        nbc.ConverterNotebook.__init__(self, infile, outbase)

    @nbc.DocInherit
    def render_code(self, cell):
        output = find_and_merge_metadata(cell)
        if (output is not None and 
            'owner' in output.json['workbook_metadata'].keys() 
            and output.json['workbook_metadata']['owner'] == 'teacher'):
            cell.input = self.cipher.encrypt(cell.input)
            for output in cell.outputs:
                # don't encrypt the metadata
                if hasattr(output, "json"):
                    try:
                        if 'workbook_metadata' not in output.json.keys():
                            output.json = self.cipher.encrypt(json.dumps(output.json))
                    except:
                        output.json = self.cipher.encrypt(json.dumps(output.json))
                        pass

        return nbc.ConverterNotebook.render_code(self, cell)

class DecryptTeacherInfo(nbc.ConverterNotebook):

    def __init__(self, infile, outbase, cipher):
        self.cipher = cipher
        nbc.ConverterNotebook.__init__(self, infile, outbase)

    @nbc.DocInherit
    def render_code(self, cell):
        output = find_and_merge_metadata(cell)
        if (output is not None and 
            'owner' in output.json['workbook_metadata'].keys()
            and output.json['workbook_metadata']['owner'] == 'teacher'):
            cell.input = self.cipher.decrypt(cell.input)
            for output in cell.outputs:
                # don't encrypt the metadata
                if hasattr(output, "json"):
                    try:
                        if 'workbook_metadata' not in output.json.keys():
                            output.json = json.loads(self.cipher.decrypt(output.json))
                    except:
                        output.json = json.loads(self.cipher.decrypt(output.json))
                        pass
        return nbc.ConverterNotebook.render_code(self, cell)

if __name__ == "__main__":

    encryptor = EncryptTeacherInfo('notebooks/leland_stanford/Assignment1.ipynb', 'encrypted')
    ofile = encryptor.render()
    decryptor = DecryptTeacherInfo(ofile, 'decrypted')
    decryptor.render()
