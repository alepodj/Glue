import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from common import WINDOW_SIZE, use_shared_assets

import glue

use_shared_assets()
glue.init('web')                     # Give folder containing web files

@glue.expose                         # Expose this function to Javascript
def handleinput(x):
    print('%s' % x)

glue.say_hello_js('connected!')   # Call a Javascript function

glue.start('main.html', size=WINDOW_SIZE)
