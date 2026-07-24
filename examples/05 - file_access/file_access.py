import os
import sys
import random

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from common import WINDOW_SIZE

import glue

glue.init('web')

@glue.expose
def pick_file(folder):
    if os.path.isdir(folder):
        return random.choice(os.listdir(folder))
    else:
        return 'Not valid folder'

glue.start('file_access.html', size=WINDOW_SIZE)
