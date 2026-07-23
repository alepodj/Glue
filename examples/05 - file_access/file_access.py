import glue, os, random

glue.init('web')

@glue.expose
def pick_file(folder):
    if os.path.isdir(folder):
        return random.choice(os.listdir(folder))
    else:
        return 'Not valid folder'

glue.start('file_access.html', size=(320, 120))
