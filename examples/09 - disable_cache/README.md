# 09 - Disable cache

Showing Glue's development-friendly cache-control behavior.

## What it demonstrates

- Serving interface assets with browser caching disabled.
- Confirming that `app.js` is fetched again after a reload.

## Files

- `disable_cache.py` — Glue entry point with the cache option shown explicitly.
- `ui/index.html` — cache status presentation.
- `ui/app.js` — reports when the script was loaded.

## Run

```powershell
cd "examples/09 - disable_cache"
python disable_cache.py
```

Reload the page and inspect the browser network panel to confirm that
`app.js` is requested again.

## Key API

```python
glue.init()
glue.start(disable_cache=True)
```

`True` is Glue's default. It is written explicitly here because cache behavior
is the feature being demonstrated; pass `False` in production when browser
caching is desired.
