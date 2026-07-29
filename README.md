# Glue
<sub>Glue is a fork of [Eel](https://github.com/python-eel/Eel) by Chris Knott and contributors.</sub>

### [Glue Documentation](https://alepodj.github.io/Glue/)

A little and opinionated Python library for making **desktop apps with HTML, CSS, and JavaScript** — plus full access to Python. It hosts a local window, then lets Python and JavaScript call each other. No new UI framework.

![Presentation — cover](assets/readme/01-cover.png)
![Presentation — pitch and simplest app](assets/readme/02-pitch.png)
![Presentation — familiar window](assets/readme/03-window.png)
![Presentation — Frontend ↔ Backend](assets/readme/04-front-to-back.png)
![Presentation — why it feels easy](assets/readme/05-why.png)

## Contents

- [Install](#install)
- [Quick start](#quick-start)
- [Demo](#demo)
- [Call both ways](#call-both-ways)
- [Hello, World!](#hello-world)
- [Return values](#return-values)
- [Settings](#settings)
- [App options](#app-options)
- [Hosts](#hosts)
- [Async Python](#async-python)
- [Package with PyInstaller](#package-with-pyinstaller)
- [Examples](#examples)
- [Project layout](#project-layout)

---

## Install

```shell
pip install glue-ui
```

That installs the **PyPI** project `glue-ui`. You still `import glue` in Python (the import name is unchanged).

From a clone of this repo:

```shell
pip install .
```

Editable / development (code changes apply without reinstalling):

```shell
pip install -e .
```

Directly from GitHub (no local clone required):

```shell
pip install "git+https://github.com/alepodj/Glue.git@main"
```

Optional extras:

```shell
pip install "glue-ui[jinja2]"   # Jinja2 templates
pip install "glue-ui[build]"    # PyInstaller for packaging
pip install "glue-ui[splash]"   # Transparent PNG/APNG/GIF startup splash
# From a clone: pip install ".[jinja2]" / ".[build]" / ".[splash]"
```

---

## Quick start

Put your frontend in a folder named `ui/` and `index.html` (the defaults), then:

```python
import glue

glue.init()    # Override ui/ with any path: glue.init('frontend')
glue.start()   # Override index.html: glue.start('main.html')
```

By default Glue opens a **PyWebView** native window. If that isn’t available, it falls back to **Chrome/Chromium** in app mode (`--app`), then **Edge** on Windows only.

Include the bridge on every html page:

```html
<script type="text/javascript" src="/glue.js"></script>
```

***Put your backend logic in one Python file or split it across any folders you like — Glue does not require a fixed backend layout. You own the imports and paths; your start point is the Python script you run (often at the project root).***

### Security note

By default Glue binds to **localhost** and only accepts Glue WebSocket clients from the loopback interface. Every `@glue.expose`d Python function is callable by any page that can open that socket — treat exposed functions as your trust boundary. Do not put secrets under the frontend folder (`ui/`). Use `all_interfaces=True` only on trusted networks (it allows remote clients to call exposed functions).

---

## Demo

The [`examples/00 - presentation`](examples/00%20-%20presentation) app is a full walkthrough of the idea. Run it with:

```shell
cd "examples/00 - presentation"
python presentation.py
```

---

## Call both ways

### Python → available in JavaScript

```python
#python
@glue.expose
def add(a, b):
    return a + b
```

```javascript
//javascript
let sum = await glue.add(1, 2)();
```

### JavaScript → available in Python

```javascript
//javascript
glue.expose(js_random);
function js_random() {
  return Math.random();
}
```

```python
#python
n = glue.js_random()()          # wait for the value
glue.js_random()(print)         # or use a callback
```

Complex values travel as JSON over a WebSocket.

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

Run `python hello.py`. Python→JS calls made before the page WebSocket connects are queued and flushed when the bridge is ready (the HTTP server is already up before the window opens).

---

## Return values

Python and the UI talk over a WebSocket. Glue gives you two ways to get a result back.

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

## Settings

Optional durable JSON for themes, defaults, and other app state that should survive restarts. **Python only** — expose your own wrappers with `@glue.expose` if the UI needs it.

The default location is opt-in via `app_name`. Without it, Glue does not invent a path; you can still load/save any file with an explicit path.

```python
import glue

glue.init(app_name='myapp')   # unlocks ~/.myapp/myapp.json (all OS)

data = glue.settings()        # {} if the file does not exist yet — nothing created on disk
data['theme'] = 'dark'
glue.save_settings(data)      # first save creates ~/.myapp/ and writes myapp.json
```

```python
# Custom file — works with or without app_name
data = glue.settings('/path/to/prefs.json')
glue.save_settings(data, '/path/to/prefs.json')
# or after settings(path), save_settings(data) reuses that path
```

- Structure of the JSON object is yours.
- `glue.settings_path()` returns the default path when `app_name` is set.
- Passing `app_name` alone does not create a folder or an empty file.

---

## App options

Pass keyword arguments to `glue.start()`:

| Option | Default | Source | Hosts | Notes |
|--------|---------|--------|-------|--------|
| *(pages)* | `'index.html'` | Glue | all | Which HTML file(s) to open first (positional args), they must come before keyword args |
| `mode` | `'auto'` | Glue | all | How to show the UI — see [Hosts](#hosts) |
| `host` | `'localhost'` | Glue | all | Hostname the local HTTP server binds to |
| `port` | `8000` | Glue | all | Server port (`0` = pick a free port) |
| `block` | `True` | Glue | all | Keep `start()` running until the app exits. `False` returns so you can run your own loop (skips PyWebView in `auto`; PyWebView needs `True`) |
| `jinja_templates` | `None` | Glue | all | Subfolder of the UI root for Jinja2 templates |
| `close_callback` | `None` | Glue | all | Called when a window/WebSocket closes (cleanup / last-window logic) |
| `all_interfaces` | `False` | Glue | all | Listen on `0.0.0.0` and allow remote WebSocket clients (trusted networks only) |
| `disable_cache` | `True` | Glue | all | Send `no-store` so the browser doesn’t cache UI assets during development |
| `default_path` | `'index.html'` | Glue | all | Page served for the root URL `/` (homepage) |
| `app` | new Bottle | Glue | all | Optional custom [Bottle](https://bottlepy.org/) app (e.g. add auth/session middleware). Omit to let Glue create one |
| `shutdown_delay` | `1.0` | Glue | all | Seconds to wait after the last window closes before the Python process exits |
| `splash` | `False` | Glue | webview / chrome / edge / custom | `True` discovers a PNG/APNG/GIF named `splash` in the UI or project root; a path selects an explicit image. Requires `glue-ui[splash]` |
| `splash_min_duration` | `1.0` | Glue | webview / chrome / edge / custom | Minimum visible seconds; readiness and this duration must both complete before fade-out (`0` disables the minimum) |
| `geometry` | `{}` | Glue | webview / chrome / edge | Per-page size/position when opening multiple files. Keys = page paths; values = `{'size': (w, h), 'position': (x, y)}` (either key optional). Overrides global `size` / `position` for that page |
| `app_mode` | `True` | Glue | chrome/edge | Open Chromium in `--app` (desktop-like, less browser chrome) |
| `cmdline_args` | `['--disable-http-cache']` | Glue | chrome/edge/custom | **Chrome/Edge:** extra flags appended to the browser command. **`custom`:** the full `Popen` argv (executable + args) |
| `frameless` | `True` | PyWebView | webview | Hide the OS title bar; Glue draws its in-page title bar (`False` = stock OS chrome) |
| `easy_drag` | `False` | PyWebView | webview | Allow dragging a frameless window from any empty area of the page |
| `shadow` | `True` on Windows | PyWebView | webview | Draw a drop shadow around the window |
| `debug` | `False` | PyWebView | webview | Enable DevTools / shortcuts (F12, F5, context menu) for debugging |
| `confirm_close` | `False` | PyWebView | webview | Ask “close this window?” before quitting |
| `fullscreen` | `False` | PyWebView | webview | Start covering the whole screen |
| `minimized` | `False` | PyWebView | webview | Start in the taskbar/dock (hidden until restored) |
| `maximized` | `False` | PyWebView | webview | Start maximized to the work area |
| `on_top` | `False` | PyWebView | webview | Keep the window above other windows |
| `min_size` | `(200, 100)` | PyWebView | webview | Smallest `(width, height)` the user can resize to |
| `icon` | `ui/favicon.ico` if present | PyWebView | webview / chrome / edge | **PyWebView:** app icon in the taskbar/dock (`.ico` / `.icns`). **Chrome/Edge:** caption icon comes from the page favicon — Glue injects `<link rel="icon" href="/favicon.ico?v=…">` into served HTML when `ui/favicon.ico` exists |
| `gui` | auto | PyWebView | webview | Force a specific web engine backend (`'edgechromium'`, `'qt'`, `'gtk'`, …) |
| `menu` | `[]` | PyWebView | webview | Native menu bar (`Menu` / `MenuAction` from PyWebView); empty = no menus |
| `webview_options` | `{}` | PyWebView | webview | Escape hatch for other [PyWebView](https://pywebview.flowrl.com/api/) kwargs; first-class kwargs win on conflict |
| `size` | `None` → **1280×720** | both | webview / chrome / edge | Initial content size as `(width, height)` pixels |
| `position` | `None` | both | webview / chrome / edge | Initial screen position as `(left, top)`; omit to leave placement to the host (usually centered) |
| `title` | `'Glue'` | both | webview | Text in the native/in-page title bar (Chrome/Edge use the page `<title>`) |
| `resizable` | `True` | both | webview | Allow the user to resize; on Windows frameless, Glue adds edge grips |

**Source Annotations:** 
- `Glue` = Glue’s own API
- `PyWebView` = A PyWebView window option that Glue exposes on glue.start() for convenience
- `both` = Glue has always offered this as a first-class glue.start() option, and when the host is PyWebView, Glue also maps it into PyWebView’s kwargs

**Hosts Annotations:** 
- Which window host honors the option (`all`, `webview`, `chrome/edge`, …).

**Defaults**: 
- What you get when you omit the argument (Glue’s opinionated window setup). Pass an explicit value to override; that also wins over the same key in `webview_options`. Glue sets `SHOW_DEFAULT_MENUS=False` so stock Edit menus stay off unless you build your own. Advanced window control: `glue.get_webview_windows()`.

### Startup splash

Install `glue-ui[splash]`, then place a PNG, APNG, or GIF named `splash` in your
project root or UI folder:

```python
import multiprocessing
import glue

def main():
    glue.init()
    glue.start(splash=True, splash_min_duration=1.0)
    # Or select a file: glue.start(splash='branding/launch.gif')

if __name__ == '__main__':
    multiprocessing.freeze_support()
    main()
```

Glue renders the image in an independent, frameless GLFW window with transparent
pixels. It fades after the initial page loads, connects, and paints, while
honoring the minimum duration. The guarded entrypoint is required by Windows
multiprocessing and works with frozen applications. Missing optional
dependencies or unavailable compositor transparency disable only the splash;
the main app continues starting.

---

## Hosts

**How Glue opens your UI** on any OS.

Default order for `mode='auto'`:

1. **PyWebView** — native window (Windows / macOS / Linux); full control via PyWebView APIs / `glue.get_webview_windows()`
2. **Chrome/Chromium** — app mode (`--app`) on all platforms
3. **Edge** — Windows only, if Chrome is missing

`size` / `position` / `geometry` apply on PyWebView as window kwargs, and on Chrome/Edge via `/glue.js` (`resizeTo` / `moveTo` on page load). When `ui/favicon.ico` is present, Glue injects a favicon `<link>` into served HTML so Chrome/Edge `--app` windows can show it in the caption.

PyWebView window options are first-class on [`glue.start()`](#app-options) (plus `webview_options` escape hatch).

| `mode` | Behavior |
|--------|----------|
| `'auto'` | PyWebView → Chrome → Edge (Windows); see above |
| `'webview'` | PyWebView only |
| `'chrome'` / `'edge'` | Force that Chromium browser |
| `None` | Server only (tests, custom frontends) |
| `'custom'` | Raw `Popen(cmdline_args)` — the full process argv (executable + args) |

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
glue.start(block=False)

while True:
    print("main")
    glue.sleep(1.0)
```

With `block=False`, `mode='auto'` skips PyWebView (its GUI loop needs the main thread) and uses Chrome/Edge instead.

---

## Package with PyInstaller

1. Use a clean virtualenv with only what you need
2. `pip install "glue-ui[build]"` (or `pip install ".[build]"` from a clone)
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
| [`11 - splash`](examples/11%20-%20splash) | Transparent GLFW startup splash |

---

## Project layout

```
my_app.py
ui/
  index.html
  css/
  js/
```

Frontend lives under one `ui/` root (by default). Backend is normal Python. Glue glues them together.
