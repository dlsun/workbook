import json

from ..external import nbconvert as nbc
import base64

# pycrypto tools

from Crypto.Cipher import AES
BLOCK_SIZE = 16
KEY_SIZE = 16
AES.block_size = BLOCK_SIZE

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
        if cell.input and cell.metadata['group'] == 'teacher':
            cell.metadata.setdefault('input_encrypted', False)
            if cell.metadata['input_encrypted'] == False:
                cell.input = self.cipher.encrypt(cell.input)
                cell.metadata['input_encrypted'] = True
        return nbc.ConverterNotebook.render_code(self, cell)

class DecryptTeacherInfo(nbc.ConverterNotebook):

    def __init__(self, infile, outbase, cipher):
        self.cipher = cipher
        nbc.ConverterNotebook.__init__(self, infile, outbase)

    @nbc.DocInherit
    def render_code(self, cell):
        if cell.input and cell.metadata['group'] == 'teacher':
            #import sys; sys.stderr.write('decrpyt: ' + `cell` + '\n')
            cell.metadata.setdefault('input_encrypted', False)
            if cell.metadata['input_encrypted'] == True:
                cell.input = self.cipher.decrypt(cell.input)
                cell.metadata['input_encrypted'] = False
        return nbc.ConverterNotebook.render_code(self, cell)

if __name__ == "__main__":

    encryptor = EncryptTeacherInfo('notebooks/leland_stanford/Assignment1.ipynb', 'encrypted')
    ofile = encryptor.render()
    decryptor = DecryptTeacherInfo(ofile, 'decrypted')
    decryptor.render()
