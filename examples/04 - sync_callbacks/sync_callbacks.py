import random

import glue

glue.init()


@glue.expose
def py_random():
    return random.random()


glue.start(block=False)

# Synchronous calls must happen after start(). Empty second parentheses wait
# for and return the JavaScript result.
n = glue.js_random()()
print('Got this from JavaScript:', n)

while True:
    glue.sleep(1.0)
