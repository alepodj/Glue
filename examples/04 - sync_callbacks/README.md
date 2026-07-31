# 04 - Synchronous callbacks

Waiting for return values from the opposite side of the Glue bridge.

## What it demonstrates

- Awaiting a Python result in JavaScript.
- Waiting for a JavaScript result in Python.
- Keeping Python active after a non-blocking start.

## Files

- `sync_callbacks.py` — Python-side synchronous call and event loop.
- `ui/index.html` — result presentation.
- `ui/app.js` — exposed JavaScript function and awaited Python call.

## Run

```powershell
cd "examples/04 - sync_callbacks"
python sync_callbacks.py
```

## Key API

```python
glue.init()
glue.start(block=False)
```

`block=False` is required so Python can continue and make its synchronous
JavaScript call after the window starts.
