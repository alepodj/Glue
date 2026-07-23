import glue

# Set web files folder
glue.init('web')

@glue.expose                         # Expose this function to Javascript
def say_hello_py(x):
    print('Hello from %s' % x)

say_hello_py('Python World!')
glue.say_hello_js('Python World!')   # Call a Javascript function

# Force Google Chrome/Chromium (app mode still on by default)
glue.start('hello.html', mode='chrome', size=(300, 200))
