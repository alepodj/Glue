# Splash API

This example uses Glue's optional transparent startup splash:

```python
glue.start(splash=LOGO_PATH)
```

Install the optional dependencies:

```powershell
python -m pip install ".[splash]"
```

Run from the repository root:

```powershell
python "examples/11 - splash/splash.py"
```

The PNG appears in a separate frameless GLFW window with true alpha, then fades
away after both conditions are met:

1. The initial Glue page has loaded, connected its bridge, and painted.
2. The default one-second minimum display time has elapsed.

`splash=True` automatically searches the UI directory and project root for a
PNG, APNG, or GIF named `splash`. An explicit relative or absolute image path
can be passed instead.

Windows multiprocessing requires the guarded entrypoint and `freeze_support()`
shown in `splash.py`. The worker stays isolated from the application and imports
neither Glue nor Bottle.
