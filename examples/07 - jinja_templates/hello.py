import os
import sys
import random

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from common import WINDOW_SIZE

import glue

glue.init()                     # Serve the ui/ folder

@glue.expose
def py_random():
    return random.random()

@glue.expose                         # Expose this function to Javascript
def say_hello_py(x):
    print('Hello from %s' % x)

say_hello_py('Python World!')
glue.say_hello_js('Python World!')   # Call a Javascript function

glue.start('templates/hello.html', size=WINDOW_SIZE, jinja_templates='templates')
