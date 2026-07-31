import random

import glue

glue.init()


@glue.expose
def py_random():
    return random.random()


@glue.expose
def say_hello_py(x):
    print('Hello from %s' % x)


say_hello_py('Python World!')
glue.say_hello_js('Python World!')

glue.start('templates/index.html', jinja_templates='templates')
