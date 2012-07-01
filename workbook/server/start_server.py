from flask import Flask, render_template, request
import os, shutil, glob, json, tempfile

from IPython.nbformat import current as nbformat
from IPython.frontend.terminal.interactiveshell import TerminalInteractiveShell

from workbook.server.answer_checker import check_answer, calculate_grade
from workbook.utils.homework_creator import create_assignment
from workbook.io import *

from workbook.converters.showhide import HideData, MergeData

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
        user_name = 'Test Student'
        user_num = '00000001'
        user_id = 'testing'
    user = {'name': user_name, 'num': user_num, 'id': user_id}
    folder = user_folder(user)
    if not os.path.exists(folder):
        generate_student(user)

    if user_id in teachers:
        user['group'] = 'teacher'
    elif user_id in tas:
        user['group'] = 'ta'
    else:
        user['group'] = 'student'
    return user

def generate_student(user):
    folder = user_folder(user)
    try:
        os.makedirs(folder)
    except OSError:
        pass

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
            create_assignment(template, user)
    nb_files = glob.glob(os.path.join(folder, '*ipynb'))

    # open up each file and calculate grade
    hw_data = []
    for nb_file in nb_files:
        nb = nbformat.read(open(nb_file, 'rb'), 'json')
        points, max_points = calculate_grade(nb)
        hw_data.append({
                'name': nb.metadata.name,
                'points': points,
                'max_points': max_points
                })

    # strip folder from the filename
    nb_files = [os.path.split(path)[1] for path in nb_files ]

    return render_template('index.html',user = user, nb_files=nb_files, hw_data=hw_data)


# load the notebook page
@app.route('/hw/<nbname>')
def hw(nbname):
    user = check_user(request)
    return render_template('homework.html',nbname = nbname)

# load the JSON file of the notebook
@app.route('/hw/<nbname>/load', methods=['GET'])
def load_nb(nbname):
    user = check_user(request)
    local_file = os.path.join(user_folder(user), nbname + '.ipynb')
    tmp_file = os.path.join(user_folder(user), nbname + '_hidden.ipynb')
    # hide all the input cells
    hidden = HideData(local_file, tmp_file[:-6])
    hidden.render()
    nb = nbformat.read(open(tmp_file, 'rb'), 'json')
    os.remove(tmp_file)
    return json.dumps(nb)

# save the JSON file of the notebook
@app.route('/hw/<nbname>/save', methods=['PUT'])
def save_nb(nbname):
    user = check_user(request)
    # save the active copy temporarily
    active_file = os.path.join(user_folder(user), nbname + "_active.ipynb")
    nb = nbformat.reads(request.data, 'json')
    nbformat.write(nb, open(active_file, 'wb'), 'json')
    local_file = os.path.join(user_folder(user), nbname + ".ipynb")
    local_nb = nbformat.read(open(local_file,'rb'), 'json')
    
    merged_file = os.path.join(user_folder(user), nbname + "_merged.ipynb")
    merged = MergeData(active_file, merged_file[:-6], local_nb)
    merged.render()

    os.rename(merged_file, local_file)
    os.remove(active_file)
    
    return request.data

# check a specific question in the notebook
@app.route('/hw/<nbname>/check', methods=['POST'])
def check_question(nbname):
    user = check_user(request)
    cell = request.json
    # load notebook
    filename = os.path.join(user_folder(user), nbname+".ipynb")
    nb = nbformat.read(open(filename, 'rb'), 'json')
    # check_answer returns a new cell to replace the old, and the updated notebook
    new_cell, nb = check_answer(cell,user,nb)
    # save the updated notebook
    nbformat.write(nb, open(filename, 'wb'), 'json')
    # return the new cell to the user
    return json.dumps(new_cell)

def initialize_shell():
    generate_student({'id':'server', 'name':'Workbook Server', 'num':0000001})
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
    app.run(debug=True,host='0.0.0.0', use_reloader=False, use_debugger=True)
    #app.run(debug=False,host='0.0.0.0')

if __name__ == "__main__":
    main()

