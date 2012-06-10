from flask import Flask, render_template, request
import os, shutil, glob, json

from IPython.nbformat import current as nbformat

PATH_TO_HW_FILES = 'notebooks/'
PATH_TO_HW_TEMPLATES = 'hw_templates/'

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
        user_id = 'anon'
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
        for hw_file in glob.glob(os.path.join(PATH_TO_HW_TEMPLATES,'*.ipynb')):
            shutil.copy(hw_file,folder)
    # get a list of all the notebooks in directory
    nbs = [ nb[:-6] for nb in os.listdir(folder) ] # strip .ipynb from filename
    return render_template('index.html',user = user,nbs=nbs)

# load the notebook page
@app.route('/hw/<nb>')
def hw(nb):
    user = check_user(request)
    return render_template('homework.html',nb = nb)

# load the JSON file of the notebook
@app.route('/hw/<nb>/load', methods=['GET'])
def load_nb(nb):
    user = check_user(request)
    filename = os.path.join(PATH_TO_HW_FILES, user['id'], nb + '.ipynb')
    nb = nbformat.read(open(filename, 'rb'), 'json')
    return json.dumps(nb)

# save the JSON file of the notebook
@app.route('/hw/<nb>/save', methods=['PUT'])
def save_nb(nb):
    user = check_user(request)
    filename = os.path.join(PATH_TO_HW_FILES, user['id'], nb + '.ipynb')
    nb = nbformat.reads(request.data, 'json')
#     for w in nb['worksheets']:
#         for c in w['cells']:
#             # now we do the reverse of the above
#             if 'input' in c:
#                 c['input'] = c['input'].split('\n')
#             if 'outputs' in c:
#                 for o in c['outputs']:
#                     if 'text' in o:
#                         o['text'] = o['text'].split('\n')
#             if 'source' in c:
#                 c['source'] = c['source'].split('\n')
#     nbs = nbformat.parse_json(request.data)
#     print 'nbs:', nbs
    nbformat.write(nb, open(filename, 'wb'), 'json')
    return request.data

# start server
if __name__ == '__main__':
    app.run(debug=True,host='0.0.0.0')
    #app.run(debug=False,host='0.0.0.0')

