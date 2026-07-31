# 06 - Input

Submitting interface input to Python and displaying its return value.

## What it demonstrates

- Handling a normal HTML form.
- Calling an exposed Python function with user input.
- Awaiting and displaying the Python response.

## Files

- `input.py` — exposed input handler and Glue entry point.
- `ui/index.html` — input form and result presentation.
- `ui/app.js` — form handling and bridge call.

## Run

```powershell
cd "examples/06 - input"
python input.py
```

## Key API

```python
glue.init()
glue.start()
```

Both startup calls use Glue's defaults.
