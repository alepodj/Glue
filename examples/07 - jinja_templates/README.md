# 07 - Jinja templates

Rendering multiple Glue pages from a shared Jinja base template.

## What it demonstrates

- Enabling a Jinja template directory.
- Extending `base.html` from multiple pages.
- Keeping the Glue bridge available on rendered templates.

## Files

- `jinja_templates.py` — exposed Python functions and Jinja configuration.
- `ui/templates/index.html` — initial rendered page.
- `ui/templates/page2.html` — secondary rendered page.
- `ui/templates/base.html` — shared document and presentation template.
- `ui/app.js` — bridge functions shared by the rendered pages.

## Run

```powershell
cd "examples/07 - jinja_templates"
python jinja_templates.py
```

## Key API

```python
glue.init()
glue.start('templates/index.html', jinja_templates='templates')
```

The custom page path and `jinja_templates` option are required because Jinja
templates live under `ui/templates/`.
