from flask import Flask, render_template, request
import os, shutil, glob, json

from IPython.nbformat import current as nbformat

# need to setup proper package structure

from workbook.converters.encrypt import EncryptTeacherInfo, DecryptTeacherInfo
from workbook.converters.owner import StudentOwner, RemoveOwner
from workbook.converters import compose_converters

from workbook.utils.homework_creator import create_assignment

PATH_TO_HW_FILES = '/Users/jonathantaylor/workbook/notebooks/'
PATH_TO_HW_TEMPLATES = '/Users/jonathantaylor/workbook/hw_templates/'
PATH_TO_HEADERS = '/Users/jonathantaylor/workbook/headers/'
PATH_TO_STUDENTS = '/Users/jonathantaylor/workbook/students/'

app = Flask(__name__)

# checks whether user is logged in and returns user information
def check_user(request):
    try:
        data = request.headers['Webauthproxy'].split(':')
        user_name = data[1]
        user_num = data[2]
        user_id = data[3][:-13]
    except KeyError:
        user_name = 'Guest User'
        user_num = '00000000'
        user_id = 'leland_stanford'
    user = {'name': user_name, 'num': user_num, 'id': user_id}
    return user

# load list of notebooks for each student
@app.route('/')
def index():    
    # parse headers to get user information
    user = check_user(request)
    # see if user has his own directory; if not, make one
    folder = os.path.join(PATH_TO_HW_FILES, user['id'])
    if not os.path.exists(folder):
        os.makedirs(folder)
        # copy files from master directory to newly made folder
        for hw_dir in glob.glob(os.path.join(PATH_TO_HW_TEMPLATES,'assignment*')):
            outfile = create_assignment(hw_dir, os.path.join(PATH_TO_HEADERS,'standard_header.ipynb'), 
                                        os.path.join(PATH_TO_STUDENTS,user['id'] + '.ipynb'))
            shutil.copy(outfile, folder)
    # get a list of all the notebooks in directory
    nb_files = glob.glob(os.path.join(folder,'*.ipynb'))
    nbs = [ nbformat.read(open(nb_file, 'rb'), 'json') for nb_file in nb_files ]
    # strip folder from the filename
    nb_files = [ os.path.split(path)[1] for path in nb_files ]
    return render_template('index.html',user = user, nb_files=nb_files, nbs=nbs)

# load the notebook page
@app.route('/hw/<nb>')
def hw(nb):
    user = check_user(request)
    return render_template('homework.html',nb = nb)

# load the JSON file of the notebook
@app.route('/hw/<nbname>/load', methods=['GET'])
def load_nb(nbname):
    user = check_user(request)
    filename = os.path.join(PATH_TO_HW_FILES, user['id'], nbname + '.ipynb')
    nb = nbformat.read(open(filename, 'rb'), 'json')
    nb = compose_converters(nb, EncryptTeacherInfo, StudentOwner)
    nb.metadata.name = nbname
    nbformat.write(nb, file('test.ipynb','wb'), 'json')
    return json.dumps(nb)

# save the JSON file of the notebook
@app.route('/hw/<nbname>/save', methods=['PUT'])
def save_nb(nbname):
    user = check_user(request)
    filename = os.path.join(PATH_TO_HW_FILES, user['id'], nbname+".ipynb")
    nb = nbformat.reads(request.data, 'json')
    nb = compose_converters(nb, RemoveOwner, DecryptTeacherInfo)
    nb.metadata.name = nbname
    nbformat.write(nb, open(filename, 'wb'), 'json')
    return request.data

# load the JSON file of the notebook
@app.route('/hw/<nb>/check', methods=['GET'])
def check_nb(nb):
    import sys
    sys.stderr.write(`request`)
    return json.dumps(nb)

# start server

def main():
    app.run(debug=True,host='0.0.0.0')
    #app.run(debug=False,host='0.0.0.0')

if __name__ == "__main__":
    main()

