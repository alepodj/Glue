# 11 - Splash

A transparent native startup splash that fades into the Glue application.

## What it demonstrates

- Auto-discovering `ui/splash.png` with `splash=True`.
- Waiting for the first painted page and a one-second minimum duration.
- Automatically centering a splash-enabled application.
- Starting the splash worker safely on Windows and in frozen applications.

## Files

- `splash.py` — guarded Glue entry point and multiprocessing setup.
- `ui/index.html` — application shown after the splash.
- `ui/splash.png` — transparent splash image.

## Install

```powershell
python -m pip install ".[splash]"
```

## Run

```powershell
cd "examples/11 - splash"
python splash.py
```

## Key API

```python
glue.init()
glue.start(splash=True)
```

`splash=True` searches the UI directory and project root for `splash.png`,
`splash.apng`, or `splash.gif`. An explicit relative or absolute image path can
be passed instead.

The guarded entry point and `multiprocessing.freeze_support()` are required by
the spawned splash renderer on Windows and in PyInstaller applications.
