import glue

glue.init()


@glue.expose
def say_hello_py(x):
    print('Hello from %s' % x)


say_hello_py('Python World!')
glue.say_hello_js('Python World!')

# Force Google Chrome/Chromium (app mode still on by default)
glue.start(mode='chrome')
