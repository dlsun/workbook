from flask import Flask, render_template, request
import os, shutil, glob, json, tempfile

from IPython.nbformat import current as nbformat
from IPython.frontend.terminal.interactiveshell import TerminalInteractiveShell

from workbook.converters.encrypt import EncryptTeacherInfo, DecryptTeacherInfo, AES, BLOCK_SIZE, KEY_SIZE, Cipher
from workbook.converters.metadata import set_group

from workbook.server.answer_checker import check_answer, get_grades
from workbook.utils.homework_creator import create_assignment
from workbook.io import *

# for constructing the encryption key, iv

import random, base64

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
    folder = user_folder(user)
    if not os.path.exists(folder):
        generate_student(user)
    set_student_cipher(user)

    if user_id in teachers:
        user['group'] = 'teacher'
    elif user_id in tas:
        user['group'] = 'ta'
    else:
        user['group'] = 'student'
    return user

def user_folder(user):
    return os.path.join(PATH_TO_HW_FILES, user['id'])

# load list of notebooks for each student
@app.route('/')
def index():    
    # parse headers to get user information
    user = check_user(request)
    # see if user has his own directory; if not, make one
    folder = user_folder(user)
    # get a list of all the notebooks in directory
    for template in glob.glob(os.path.join(PATH_TO_HW_TEMPLATES,'*.ipynb')):
        student_file = os.path.join(folder, os.path.split(template)[1])
        if not os.path.exists(student_file):
            generate_assignment(template, user)
    nb_files = glob.glob(os.path.join(folder, '*ipynb'))
    nbs = [ nbformat.read(open(nb_file, 'rb'), 'json') for nb_file in nb_files ]
    # strip folder from the filename
    nb_files = [os.path.split(path)[1] for path in nb_files ]

    return render_template('index.html',user = user, nb_files=nb_files, nbs=nbs)

def generate_student(user):
    #StudentCreator(user['id'], user['name']).render()
    folder = user_folder(user)
    try:
        os.makedirs(folder)
    except OSError:
        pass

    # make encryption data

    key = base64.b64encode(unicode.encode(
            ''.join([unichr(random.choice((0x300, 0x2000))
                            +random.randint(0,0xff)) for _ in range(KEY_SIZE)]), 'utf-8'))[:KEY_SIZE]

    iv = base64.b64encode(unicode.encode(
            ''.join([unichr(random.choice((0x300, 0x2000))
                            +random.randint(0,0xff)) for _ in range(BLOCK_SIZE)]), 'utf-8'))[:BLOCK_SIZE]

    open(os.path.join(folder, 'student_info.json'), 'wb').write(json.dumps({'key':key,
                                                                            'iv':iv,
                                                                            'name':user['name'],
                                                                            'id':user['id'],
                                                                            'seed':random.randint(0,1000000)}))

def generate_assignment(hwtemplate, user):
    folder = user_folder(user)
    outfile = create_assignment(hwtemplate, os.path.join(folder, 'student_info.json'))

def set_student_cipher(user):

    folder = user_folder(user)
    d = json.load(open(os.path.join(folder, 'student_info.json'), 'rb'))
    key = d['key']
    iv = d['iv']
    user['cipher'] = Cipher(key, iv)

# load the notebook page
@app.route('/hw/<nbname>')
def hw(nbname):
    user = check_user(request)
    return render_template('homework.html',nbname = nbname)

def forward(nb, filename, user, nbname):
    """
    converters in forward direction

    """

    # first add the teacher workbook info

    encrypt = EncryptTeacherInfo(filename, 'encrypt', user['cipher']) 
    encrypt.render()
    os.rename('encrypt.ipynb', filename)

    nb = nbformat.read(open(filename, 'rb'), 'json')
    nb.metadata.name = nbname
    nbformat.write(nb, open(filename, 'wb'), 'json')
 
    return nb


def reverse(nb, filename, user, nbname):
    """
    converters in reverse direction

    """
    decrypt = DecryptTeacherInfo(filename, 'decrypt', user['cipher']) 
    decrypt.render()
    os.rename('decrypt.ipynb', filename)

#    owner = set_group(filename, 'owner', user['group'])
#    owner.render()
#    os.rename('owner.ipynb', filename)
    
    nb = nbformat.read(open(filename, 'rb'), 'json')
    return nb

# load the JSON file of the notebook
@app.route('/hw/<nbname>/load', methods=['GET'])
def load_nb(nbname):
    user = check_user(request)
    filename = os.path.join(user_folder(user), nbname + '.ipynb')
    nb = nbformat.read(open(filename, 'rb'), 'json')
    nb = forward(nb, filename, user, nbname)
    return json.dumps(nb)

# save the JSON file of the notebook
@app.route('/hw/<nbname>/save', methods=['PUT'])
def save_nb(nbname):
    user = check_user(request)
    filename = os.path.join(user_folder(user), nbname+".ipynb")
    nb = nbformat.reads(request.data, 'json')
    nbformat.write(nb, open(filename, 'wb'), 'json')
    # import sys; sys.stderr.write('\nnb: ' + nbformat.writes(nb, 'json') + '\n')
    nb = reverse(nb, filename, user, nbname)
    nbformat.write(nb, open(filename, 'wb'), 'json')
    
    return request.data

# check a specific question in the notebook
@app.route('/hw/<nbname>/check', methods=['POST'])
def check_nb_question(nbname):
    user = check_user(request)
    filename = os.path.join(user_folder(user), nbname + '.ipynb')

    identifier = request.json['metadata']['identifier']
    answer = request.json['metadata']['answer']
    # check_answer should return a JSON file containing the new cell 
    cell = request.json
    new_cell_json = check_answer(cell, user)
    return json.dumps(new_cell_json)

# grade a specific question in the notebook
@app.route('/hw/<nbname>/grade', methods=['POST'])
def grade_nb_question(nbname):
    user = check_user(request)
    filename = os.path.join(user_folder(user), nbname + '.ipynb')

    identifier = request.json['metadata']['identifier']
    answer = request.json['metadata']['answer']
    # check_answer should return a JSON file containing the new cell 
    cell = request.json
    grades, new_cell_json = get_grades(cell, user)
    import sys; sys.stderr.write('\ngrades: ' + `grades` + '\n')
    return json.dumps(new_cell_json)

# grade a specific question in the notebook
@app.route('/hw/<nbname>/gradebook', methods=['PUT'])
def grade_nb(nbname):
    user = check_user(request)
    filename = os.path.join(user_folder(user), nbname+".ipynb")
    nb = nbformat.reads(request.data, 'json')
    grades = []
    for ws in nb.worksheets:
        for cell in ws.cells:
            if (hasattr(cell, 'input') and hasattr(cell, 'metadata') and 
                'identifier' in cell.metadata):
                grades.append(get_grades(cell, user)[0])
    import sys; sys.stderr.write('\ngrades: ' + `grades` + '\n')
    return request.data


def initialize_shell():
    generate_student({'id':'server', 'name':'Workbook Server'})
    shell = TerminalInteractiveShell()
    for ipynb in glob.glob(os.path.join(PATH_TO_HW_TEMPLATES, '*ipynb')):
        nb = nbformat.read(open(ipynb, 'rb'), 'json')
        for ws in nb.worksheets:
            for cell in ws.cells:
                if hasattr(cell, 'input'):
                    shell.run_cell(cell.input)
    return shell

# start server

def main():
    initialize_shell() # this loads all assignments into question_types so they can be regenerated as instances later
    app.run(debug=True,host='0.0.0.0', use_reloader=True, use_debugger=True)
    #app.run(debug=False,host='0.0.0.0')

if __name__ == "__main__":
    main()

