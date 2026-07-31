import os
import random

import glue

glue.init()


@glue.expose
def pick_file(folder):
    folder = os.path.expanduser(folder)
    if os.path.isdir(folder):
        files = [name for name in os.listdir(folder) if os.path.isfile(os.path.join(folder, name))]
        return random.choice(files) if files else 'The folder contains no files'
    return 'Not a valid folder'


glue.start()
