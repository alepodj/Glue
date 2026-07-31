# 01 - Hello world

The smallest two-way Glue application.

## What it demonstrates

- Exposing a Python function to JavaScript.
- Exposing a JavaScript function to Python.
- Starting a default Glue application from `ui/index.html`.

## Files

- `hello_world.py` — Glue entry point and exposed Python function.
- `ui/index.html` — application markup.
- `ui/app.js` — exposed JavaScript function and bridge calls.

## Run

```powershell
cd "examples/01 - hello_world"
python hello_world.py
```

## Key API

```python
glue.init()
glue.start()
```

Both calls use Glue's defaults.
