import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from common import WINDOW_SIZE, use_shared_assets

import glue

use_shared_assets()

# Set web files folder
glue.init('web')

@glue.expose                         # Expose this function to Javascript
def say_hello_py(x):
    print('Hello from %s' % x)

say_hello_py('Python World!')
glue.say_hello_js('Python World!')   # Call a Javascript function

# Force Google Chrome/Chromium (app mode still on by default)
glue.start('hello.html', mode='chrome', size=WINDOW_SIZE)
