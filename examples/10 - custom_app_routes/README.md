# 10 - Custom application routes

Combining Glue's routes with a custom Bottle application.

## What it demonstrates

- Passing an existing Bottle application to Glue.
- Calling a custom JSON route from the interface.
- Keeping Glue's static files and bridge routes available.

## Files

- `custom_app_routes.py` — Bottle route and Glue entry point.
- `ui/index.html` — route demonstration interface.
- `ui/app.js` — request to the custom route.

## Run

```powershell
cd "examples/10 - custom_app_routes"
python custom_app_routes.py
```

## Key API

```python
app = bottle.Bottle()
glue.init()
glue.start(app=app)
```

The `app` option is required because supplying a custom Bottle application is
the feature this example demonstrates.
