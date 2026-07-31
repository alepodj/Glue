# 03 - Callbacks

Asynchronous values and errors crossing the Glue bridge in both directions.

## What it demonstrates

- Passing named and inline callbacks to bridge calls.
- Using promises for Python results.
- Receiving Python and JavaScript exceptions.

## Files

- `callbacks.py` — exposed Python functions and Python-side callbacks.
- `ui/index.html` — callback result presentation.
- `ui/app.js` — exposed JavaScript functions, callbacks, and promises.

## Run

```powershell
cd "examples/03 - callbacks"
python callbacks.py
```

## Key API

```python
glue.init()
glue.start()
```

The application uses only Glue's startup defaults; callback behavior lives in
the exposed functions.
