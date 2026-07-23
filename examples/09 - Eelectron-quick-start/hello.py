import glue
# Set web files folder
glue.init('web')

@glue.expose                         # Expose this function to Javascript
def say_hello_py(x):
    print('Hello from %s' % x)

say_hello_py('Python World!')
glue.say_hello_js('Python World!')   # Call a Javascript function

glue.start('hello.html',mode='electron')
#glue.start('hello.html', mode='custom', cmdline_args=['node_modules/electron/dist/electron.exe', '.'])
