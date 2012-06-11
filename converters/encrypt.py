import sys
sys.path.append('/Users/jonathantaylor/nbconvert')

import nbconvert as nbc
import base64

# pycrypto tools

from Crypto import Random
from Crypto.Cipher import AES

class Cipher(object):

    def __init__(self):
        self.key = b'Sixteen byte key'
        self.iv = Random.new().read(AES.block_size)
        self.cipher = AES.new(self.key, AES.MODE_CFB, self.iv)

    def encrypt(self, msg):
        # pad with "[" as an unlikely end character as we are encrypting json
        # http://www.codekoala.com/blog/2009/aes-encryption-python-using-pycrypto/
        padded_msg = ']'*16 + msg + (AES.block_size - len(msg) % AES.block_size) * '['
        return base64.b64encode(self.cipher.encrypt(padded_msg))

    def decrypt(self, msg):
        decrypted_msg = self.cipher.decrypt(base64.b64decode(msg)).rstrip('[')
        return decrypted_msg[16:]

class EncryptTeacherInfo(nbc.ConverterNotebook):

    @nbc.DocInherit
    def render_code(self, cell):
        cell.input = cipher.encrypt(cell.input)
        return nbc.ConverterNotebook.render_code(self, cell)

class DecryptTeacherInfo(nbc.ConverterNotebook):

    @nbc.DocInherit
    def render_code(self, cell):
        cell.input = cipher.decrypt(cell.input)
        return nbc.ConverterNotebook.render_code(self, cell)

if __name__ == "__main__":

    encryptor = EncryptTeacherInfo('notebooks/leland_stanford/Assignment1.ipynb', 'encrypted')
    ofile = encryptor.render()
    decryptor = DecryptTeacherInfo(ofile, 'decrypted')
    decryptor.render()
