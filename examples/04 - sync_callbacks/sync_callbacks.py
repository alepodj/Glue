import os
import sys
import random

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from common import WINDOW_SIZE, use_shared_assets

import glue

use_shared_assets()
glue.init('web')

@glue.expose
def py_random():
    return random.random()

glue.start('sync_callbacks.html', block=False, size=WINDOW_SIZE)

# Synchronous calls must happen after start() is called

# Get result returned synchronously by
# passing nothing in second brackets
#                   v
n = glue.js_random()()
print('Got this from Javascript:', n)

while True:
    glue.sleep(1.0)
