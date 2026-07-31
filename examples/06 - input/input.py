import glue

glue.init()


@glue.expose
def handle_input(value):
    print(value)
    return 'Received by Python: %s' % value


glue.start()
