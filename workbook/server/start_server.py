from flask import Flask, render_template, request
import os, shutil, glob, json, tempfile

from IPython.nbformat import current as nbformat

# need to setup proper package structure

from workbook.converters.encrypt import EncryptTeacherInfo, DecryptTeacherInfo, AES, BLOCK_SIZE, KEY_SIZE, Cipher
from workbook.converters.metadata import StudentMetadata, RemoveMetadata
from workbook.converters.student_creator import StudentCreator
from workbook.converters import compose_converters, ConverterNotebook

from workbook.utils.homework_creator import create_assignment
from workbook.utils.questions import find_identified_cell, construct_question

# for constructing the encryption key, iv

import random, base64

datadir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

PATH_TO_HW_FILES = os.path.join(datadir, 'notebooks')
PATH_TO_HW_TEMPLATES = os.path.join(datadir, 'hw_templates')
PATH_TO_HEADERS = os.path.join(datadir, 'headers')
PATH_TO_STUDENTS = os.path.join(datadir, 'students')

counter = 0

app = Flask(__name__)

def debug():
    assert app.debug == False

# checks whether user is logged in and returns user information
def check_user(request):
    try:
        data = request.headers['Webauthproxy'].split(':')
        user_name = data[1]
        user_num = data[2]
        user_id = data[3][:-13]
    except KeyError:
        user_name = 'Testing student'
        user_num = '00000000'
        user_id = 'testing'
    user = {'name': user_name, 'num': user_num, 'id': user_id}
    folder = os.path.join(PATH_TO_HW_FILES, user['id'])
    if not os.path.exists(folder):
        generate_student(user, folder)
    set_student_cipher(user, folder)
    return user

# load list of notebooks for each student
@app.route('/')
def index():    
    # parse headers to get user information
    user = check_user(request)
    # see if user has his own directory; if not, make one
    folder = os.path.join(PATH_TO_HW_FILES, user['id'])
    # get a list of all the notebooks in directory
    nb_files = glob.glob(os.path.join(folder,'*.ipynb'))
    nbs = [ nbformat.read(open(nb_file, 'rb'), 'json') for nb_file in nb_files ]
    # strip folder from the filename
    nb_files = [ os.path.split(path)[1] for path in nb_files ]
    return render_template('index.html',user = user, nb_files=nb_files, nbs=nbs)

def generate_student(user, folder):
    StudentCreator(user['id'], user['name']).render()
    os.makedirs(folder)

    # make encryption data

    key = base64.b64encode(unicode.encode(
            ''.join([unichr(random.choice((0x300, 0x2000))
                            +random.randint(0,0xff)) for _ in range(KEY_SIZE)]), 'utf-8'))[:KEY_SIZE]

    iv = base64.b64encode(unicode.encode(
            ''.join([unichr(random.choice((0x300, 0x2000))
                            +random.randint(0,0xff)) for _ in range(BLOCK_SIZE)]), 'utf-8'))[:BLOCK_SIZE]

    open(os.path.join(folder, 'encryption.json'), 'wb').write(json.dumps({'key':key,
                                                             'iv':iv}))

    # copy files from master directory to newly made folder
    for hw_dir in glob.glob(os.path.join(PATH_TO_HW_TEMPLATES,'assignment*')):
        outfile = create_assignment(hw_dir, os.path.join(PATH_TO_HEADERS,'standard_header.ipynb'), 
                                    os.path.join(PATH_TO_STUDENTS,user['id'] + '.ipynb'))
        shutil.copy(outfile, folder)

def set_student_cipher(user, folder):

    d = json.load(open(os.path.join(folder, 'encryption.json'), 'rb'))
    key = d['key']
    iv = d['iv']
    user['cipher'] = Cipher(key, iv)

# load the notebook page
@app.route('/hw/<nb>')
def hw(nb):
    user = check_user(request)
    return render_template('homework.html',nb = nb)

def forward(nb, filename, user, nbname):
    """
    converters in forward direction

    """

    # filenames of converters will be adjusted by  compose_converters

    encrypt = EncryptTeacherInfo(filename, 'encrypt', user['cipher']) 
    student = StudentMetadata(filename, 'student')
    
    # composition is right to left
    nb = compose_converters(nb, student, encrypt)
    nb.metadata.name = nbname

    return nb


def reverse(nb, filename, user, nbname):
    """
    converters in reverse direction

    """
    # filenames of converters will be adjusted by  compose_converters

    decrypt = DecryptTeacherInfo(filename, 'decrypt', user['cipher']) 
    rm_meta = RemoveMetadata(filename, 'rm_meta')
    
    # composition is right to left
    nb = compose_converters(nb, decrypt, rm_meta)
    nb.metadata.name = nbname

    return nb

# load the JSON file of the notebook
@app.route('/hw/<nbname>/load', methods=['GET'])
def load_nb(nbname):
    global counter
    user = check_user(request)
    filename = os.path.join(PATH_TO_HW_FILES, user['id'], nbname + '.ipynb')
    nb = nbformat.read(open(filename, 'rb'), 'json')
    nb = forward(nb, filename, user, nbname)
    return json.dumps(nb)

# save the JSON file of the notebook
@app.route('/hw/<nbname>/save', methods=['PUT'])
def save_nb(nbname):
    global counter
    user = check_user(request)
    filename = os.path.join(PATH_TO_HW_FILES, user['id'], nbname+".ipynb")
    nb = nbformat.reads(request.data, 'json')
    nb = reverse(nb, filename, user, nbname)
    nbformat.write(nb, open(filename, 'wb'), 'json')
    return request.data

# load the JSON file of the notebook
@app.route('/hw/<nbname>/check', methods=['GET', 'POST'])
def check_nb(nbname):
    global counter
    user = check_user(request)
    filename = os.path.join(PATH_TO_HW_FILES, user['id'], nbname + '.ipynb')
    tmpf = os.path.splitext(filename)[0] + '_tmp'
    converter = ConverterNotebook(filename, tmpf)
    converter.read()
    answers = {}
    for identifier, answer in request.json:
        cell, output = find_identified_cell(converter.nb, identifier)
        answers[identifier] = {'submitted_answer': answer, 'correct_answer': output.json.correct_answer, 'constructor_info':output.json.constructor_info}
        name, args, kw = output.json.constructor_info
        question = construct_question(name, args, kw)
        data = question.check_answer(answer)
        # would be nice to automatically have this done
        output.json = data['application/json'] # json.dumps(data['application/json'])
        output.latex = data['text/latex'].split('\n')
        output.html = data['text/html'].split('\n')
    ofile = converter.render()
    os.rename(ofile, filename)
    nb = nbformat.read(open(filename, 'rb'), 'json')
    return json.dumps(nb)

# start server

def main():
    app.run(debug=True,host='0.0.0.0', use_reloader=False, use_debugger=True)
    #app.run(debug=False,host='0.0.0.0')

if __name__ == "__main__":
    main()

