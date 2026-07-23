import glue
import random

glue.init('web')

@glue.expose
def py_random():
    return random.random()

@glue.expose
def py_exception(error):
    if error:
        raise ValueError("Test")
    else:
        return "No Error"

def print_num(n):
    print('Got this from Javascript:', n)


def print_num_failed(error, stack):
    print("This is an example of what javascript errors would look like:")
    print("\tError: ", error)
    print("\tStack: ", stack)

# Call Javascript function, and pass explicit callback function    
glue.js_random()(print_num)

# Do the same with an inline callback
glue.js_random()(lambda n: print('Got this from Javascript:', n))

# Show error handling
glue.js_with_error()(print_num, print_num_failed)


glue.start('callbacks.html', size=(400, 300))

