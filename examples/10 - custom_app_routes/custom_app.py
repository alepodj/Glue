import glue
import bottle
# from beaker.middleware import SessionMiddleware

app = bottle.Bottle()
@app.route('/custom')
def custom_route():
    return 'Hello, World!'

glue.init('web')

# need to manually add glue routes if we are wrapping our Bottle instance with middleware
# glue.register_glue_routes(app)
# middleware = SessionMiddleware(app)
# glue.start('index.html', app=middleware)

glue.start('index.html', app=app)
