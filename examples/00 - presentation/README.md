# 00 - Presentation

A 1080p visual walkthrough of Glue and its Python ↔ JavaScript bridge.

## What it demonstrates

- A polished desktop-style interface built with ordinary web assets.
- Calls from JavaScript to Python and from Python to JavaScript.
- An explicit 1920×1080 presentation window.

## Files

- `presentation.py` — Glue entry point and exposed Python functions.
- `ui/index.html` — application markup.
- `ui/app.js` — presentation behavior and bridge calls.
- `ui/styles.css` — presentation-specific styling.

## Run

```powershell
cd "examples/00 - presentation"
python presentation.py
```

## Key API

```python
glue.init()
glue.start(size=(1920, 1080))
```

The explicit size is intentional because this example is designed as a 1080p
presentation.
