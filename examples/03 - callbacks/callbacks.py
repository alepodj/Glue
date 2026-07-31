import random

import glue

glue.init()


@glue.expose
def py_random():
    return random.random()


@glue.expose
def py_exception(error):
    if error:
        raise ValueError('Test')
    return 'No Error'


def print_num(n):
    print('Got this from JavaScript:', n)


def print_num_failed(error, stack):
    print('This is an example of what JavaScript errors look like:')
    print('\tError: ', error)
    print('\tStack: ', stack)


# Call a JavaScript function and pass an explicit callback.
glue.js_random()(print_num)

# Do the same with an inline callback
glue.js_random()(lambda n: print('Got this from JavaScript:', n))

# Show error handling
glue.js_with_error()(print_num, print_num_failed)


glue.start()
