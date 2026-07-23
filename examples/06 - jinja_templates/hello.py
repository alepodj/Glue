import random

import glue

glue.init('web')                     # Give folder containing web files

@glue.expose
def py_random():
    return random.random()

@glue.expose                         # Expose this function to Javascript
def say_hello_py(x):
    print('Hello from %s' % x)

say_hello_py('Python World!')
glue.say_hello_js('Python World!')   # Call a Javascript function

glue.start('templates/hello.html', size=(300, 200), jinja_templates='templates')    # Start
