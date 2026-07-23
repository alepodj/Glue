import glue, random

glue.init('web')

@glue.expose
def py_random():
    return random.random()

glue.start('sync_callbacks.html', block=False, size=(400, 300))

# Synchronous calls must happen after start() is called

# Get result returned synchronously by 
# passing nothing in second brackets
#                   v
n = glue.js_random()()
print('Got this from Javascript:', n)

while True:
    glue.sleep(1.0)
