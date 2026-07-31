# 05 - File access

Using Python filesystem access from a web-based interface.

## What it demonstrates

- Sending a folder path from JavaScript to Python.
- Reading local files with Python.
- Returning a filename to the interface.

## Files

- `file_access.py` — exposed filesystem function and Glue entry point.
- `ui/index.html` — folder form and result presentation.
- `ui/app.js` — form handling and bridge call.

## Run

```powershell
cd "examples/05 - file_access"
python file_access.py
```

## Key API

```python
glue.init()
glue.start()
```

The example uses Glue's startup defaults; filesystem access is implemented by
the exposed Python function.
