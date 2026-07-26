import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
import glue

glue.init()                     # Serve the ui/ folder

@glue.expose                         # Expose this function to Javascript
def handleinput(x):
    print('%s' % x)

glue.say_hello_js('connected!')   # Call a Javascript function

glue.start('main.html')
