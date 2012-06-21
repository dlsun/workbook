import os

# this should be read from some config file
datadir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

PATH_TO_HW_FILES = os.path.join(datadir, 'notebooks')
PATH_TO_HW_TEMPLATES = os.path.join(datadir, 'hw_templates')
PATH_TO_HEADERS = os.path.join(datadir, 'headers')
PATH_TO_STUDENTS = os.path.join(datadir, 'students')

teachers = ['jtaylo']
tas = ['dlsun', 'ncray']
students = ['testing']
