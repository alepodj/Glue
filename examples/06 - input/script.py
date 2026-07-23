import glue

glue.init('web')                     # Give folder containing web files

@glue.expose                         # Expose this function to Javascript
def handleinput(x):
    print('%s' % x)

glue.say_hello_js('connected!')   # Call a Javascript function

glue.start('main.html', size=(500, 200))    # Start
