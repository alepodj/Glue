import bottle

import glue

app = bottle.Bottle()


@app.route('/custom')
def custom_route():
    return {'message': 'Hello from a custom Bottle route'}


glue.init()

# A plain Bottle app is registered automatically. If middleware wraps the app,
# register Glue's routes on the inner Bottle instance first:
# glue.register_glue_routes(app)
# from beaker.middleware import SessionMiddleware
# middleware = SessionMiddleware(app)
# glue.start(app=middleware)

glue.start(app=app)
