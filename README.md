# Glue

A little Python library for making **desktop apps with HTML, CSS, and JavaScript** — plus full access to Python.

Glue hosts a local window, then lets Python and JavaScript call each other. No Electron ceremony. No new UI framework.

<sub>Glue is a fork of [Eel](https://github.com/python-eel/Eel) by Chris Knott and contributors.</sub>

```python
import glue

glue.init()
glue.start('index.html')
```

That is enough to open a desktop window from a folder of UI files.

---

## See it

The [`examples/00 - presentation`](examples/00%20-%20presentation) app is a full walkthrough of the idea. Run it with:

```shell
cd "examples/00 - presentation"
python presentation.py
```

### 1 · Cover

Brand, slogan, and version — the desktop window opens on the cover.

![Presentation — cover](assets/readme/01-cover.png)

### 2 · The pitch + three lines

If you already speak the web, you already speak desktop. The simplest Glue app is three lines of Python.

![Presentation — pitch and simplest app](assets/readme/02-pitch.png)

### 3 · Familiar window

Classic desktop chrome you can build yourself — Windows, macOS, and Linux styles.

![Presentation — familiar window](assets/readme/03-window.png)

### 4 · Front → Back

JavaScript calls an exposed Python function and reads the return value.

![Presentation — JavaScript calls Python](assets/readme/04-front-to-back.png)

### 5 · Back → Front

Python calls an exposed JavaScript function the same way.

![Presentation — Python calls JavaScript](assets/readme/05-back-to-front.png)

### 6 · Why it feels easy

Your technologies stay the same. Python does the hard parts. Ships as an app.

![Presentation — why it feels easy](assets/readme/06-why.png)

### 7 · Less framework. More Glue.

Start with a folder of UI files and a short Python script. That is the whole idea.

![Presentation — close](assets/readme/07-close.png)

---

## Install

From this repo:

```shell
pip install .
```

Editable / development:

```shell
pip install -e .
```

Directly from GitHub:

```shell
pip install "git+https://github.com/alepodj/Glue.git@main"
```

Optional Jinja2 templates:

```shell
pip install ".[jinja2]"
```

PyInstaller packaging helpers:

```shell
pip install ".[build]"
```

---

## Quick start

Put your frontend in a folder named `ui/` (the default), then:

```python
import glue

glue.init()
glue.start('index.html')
```

By default Glue opens **Chrome/Chromium** in app mode (`--app`). On Windows, **Edge** is used only if Chrome is missing. On macOS/Linux, Chrome/Chromium is required.

Include the bridge on every page:

```html
<script type="text/javascript" src="/glue.js"></script>
```

---

## Call both ways

### Python → available in JavaScript

```python
@glue.expose
def add(a, b):
    return a + b
```

```javascript
let sum = await glue.add(1, 2)();
```

### JavaScript → available in Python

```javascript
glue.expose(js_random);
function js_random() {
  return Math.random();
}
```

```python
n = glue.js_random()()          # wait for the value
glue.js_random()(print)         # or use a callback
```

Complex values travel as JSON over a websocket.

If a JS bundler renames functions, expose them with an explicit name:

```javascript
glue.expose(someFunction, "my_javascript_function");
```

---

## Hello, World!

Full example: [`examples/01 - hello_world`](examples/01%20-%20hello_world)

**`ui/hello.html`**

```html
<!DOCTYPE html>
<html>
  <head>
    <title>Hello, World!</title>
    <script type="text/javascript" src="/glue.js"></script>
    <script type="text/javascript">
      glue.expose(say_hello_js);
      function say_hello_js(x) {
        console.log("Hello from " + x);
      }

      say_hello_js("Javascript World!");
      glue.say_hello_py("Javascript World!");
    </script>
  </head>
  <body>Hello, World!</body>
</html>
```

**`hello.py`**

```python
import glue

glue.init()

@glue.expose
def say_hello_py(x):
    print('Hello from %s' % x)

say_hello_py('Python World!')
glue.say_hello_js('Python World!')

glue.start('hello.html')
```

Run `python hello.py`. Calls made before the window opens are queued until the websocket is ready.

---

## Return values

Python and the browser are separate processes. Glue gives you two ways to get a result back.

**Callback**

```python
glue.js_random()(lambda n: print('Got', n))
```

**Synchronous wait** (after `glue.start()`, or with `block=False`)

```python
n = glue.js_random()()
```

In JavaScript, use `async` / `await`:

```javascript
let n = await glue.py_random()();
```

Python waits up to 10 seconds for a JS result by default (`js_result_timeout` on `glue.init`).

---

## App options

Pass keyword arguments to `glue.start()`:

| Option | Default | Notes |
|--------|---------|--------|
| `mode` | `'auto'` | `'auto'`, `'chrome'`, `'edge'`, `'custom'`, or `None`/`False` (no window) |
| `host` | `'localhost'` | Bottle bind host |
| `port` | `8000` | Use `0` to pick automatically |
| `block` | `True` | Set `False` to keep running your own loop |
| `size` | `None` | `(width, height)` in pixels |
| `position` | `None` | `(left, top)` in pixels |
| `app_mode` | `True` | Chromium `--app` desktop-like window |
| `cmdline_args` | `['--disable-http-cache']` | Extra browser flags |
| `jinja_templates` | `None` | Folder name for Jinja2 templates |
| `geometry` | `{}` | Per-page size/position |
| `close_callback` | `None` | Called when a window closes |
| `app` | new Bottle | Pass your own Bottle app / middleware |
| `shutdown_delay` | `1.0` | Seconds to wait before exit when the last window closes |

Example:

```python
glue.start(
    'main.html',
    mode='chrome',
    size=(1280, 720),
    cmdline_args=['--start-fullscreen'],
)
```

---

## Browsers

Glue targets the Chromium family only:

- **`auto`** — Chrome/Chromium first; Edge only as a Windows fallback
- **`chrome`** / **`edge`** — force one browser
- **`None` / `False`** — server only (tests, custom frontends)
- **`custom`** — your own command via `cmdline_args`

Electron and other browsers are not supported.

Try [`01 - hello_world`](examples/01%20-%20hello_world) for auto launch, or [`02 - hello_world_chrome`](examples/02%20-%20hello_world_chrome) to force Chrome.

---

## Async Python

Glue uses Bottle + Gevent. Prefer `glue.sleep()` and `glue.spawn()` over `time.sleep()`.

If you need Gevent monkey-patching, do it **before** importing Glue:

```python
from gevent import monkey
monkey.patch_all()
import glue
```

```python
import glue
glue.init()

def ticker():
    while True:
        print("tick")
        glue.sleep(1.0)

glue.spawn(ticker)
glue.start('main.html', block=False)

while True:
    print("main")
    glue.sleep(1.0)
```

---

## Package with PyInstaller

1. Use a clean virtualenv with only what you need
2. `pip install ".[build]"`
3. From your app folder: `python -m glue your_script.py ui`
4. Check `dist/`, then ship with `--onefile --noconsole` when ready

Extra PyInstaller flags pass through, for example:

```shell
python -m glue file_access.py ui --exclude numpy --onefile --noconsole
```

See the [PyInstaller docs](https://pyinstaller.readthedocs.io/) for more.

---

## Examples

| Example | What it shows |
|---------|----------------|
| [`00 - presentation`](examples/00%20-%20presentation) | Full product story (screenshots above) |
| [`01 - hello_world`](examples/01%20-%20hello_world) | Minimal two-way hello |
| [`02 - hello_world_chrome`](examples/02%20-%20hello_world_chrome) | Force Chrome |
| [`03 - callbacks`](examples/03%20-%20callbacks) | Async callbacks |
| [`04 - sync_callbacks`](examples/04%20-%20sync_callbacks) | Blocking returns |
| [`05 - file_access`](examples/05%20-%20file_access) | Python file access from the UI |
| [`06 - input`](examples/06%20-%20input) | Live input bridge |
| [`07 - jinja_templates`](examples/07%20-%20jinja_templates) | Jinja2 pages |
| [`08 - createreactapp`](examples/08%20-%20createreactapp) | React + TypeScript |
| [`09 - disable_cache`](examples/09%20-%20disable_cache) | Cache control |
| [`10 - custom_app_routes`](examples/10%20-%20custom_app_routes) | Custom Bottle routes |

---

## Project layout for an app

```
my_app.py
ui/
  index.html
  css/
  js/
```

Frontend lives under one `ui/` root (by default). Backend is normal Python. Glue glues them together.
