# 02 - Hello world in Chrome

The hello-world bridge example with Chrome selected explicitly.

## What it demonstrates

- The same two-way bridge used by the default hello-world example.
- Forcing Chrome app mode instead of automatic host selection.

## Files

- `hello_world_chrome.py` — Glue entry point and Chrome mode selection.
- `ui/index.html` — application markup.
- `ui/app.js` — exposed JavaScript function and bridge calls.

## Run

```powershell
cd "examples/02 - hello_world_chrome"
python hello_world_chrome.py
```

## Key API

```python
glue.init()
glue.start(mode='chrome')
```

`mode='chrome'` is the only non-default option because it is the feature this
example demonstrates.
