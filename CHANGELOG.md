# Change log

### 0.6.3

* Fix PyWebView host: do **not** pass `icon=` to `create_window()` (unsupported on PyWebView 6.x — that TypeError made `auto` fall back to Chrome). Keep native icon on `webview.start(icon=…)` only; in-page title bar still uses `/favicon.ico`.

### 0.6.2

* Fix Chrome/Edge fallback after PyWebView: `_run_browser` calls `browsers_launcher.run` (chrome/edge modules only locate the binary).

### 0.6.1

* PyWebView: pass `ui/favicon.ico` (or explicit `icon=`) to both `create_window` and `webview.start` so native window icons work on backends that read either path.
* GitHub issue templates refreshed; add `.github/ISSUE_TEMPLATE/config.yml` (blank issues off, doc links).

### 0.6.0

* **Breaking:** Require **Python 3.10+** (drop 3.7–3.9). CI/Tox matrix: 3.10–3.14.
* Use stdlib `importlib.resources` and `typing.TypeAlias` / `TypedDict`; drop `importlib_resources` and `typing_extensions` dependencies.
* Reorganize tests into `test_<area>` modules (`init`, `expose`, `browsers`, `webview`, `security`, `settings`, `routes`); helpers under `tests/helpers/`; rename integration cases; add coverage for modes, routes, cache headers, RPC, and default window size.
* Add **Ruff** (lint + format) via `pyproject.toml`; Tox envs `lint` / `typecheck` / `py310`–`py314`; CI runs lint and typecheck as separate jobs.
* Tox on Windows: pass/set `USERNAME` for Python 3.13+ `tmp_path`; require pytest 8.1+; drop unused `tox-pyenv` (removes pyenv noise).
* Use pyparsing snake_case APIs (`nested_expr`, `parse_string`, …) so the suite runs without deprecation warnings.
* Expand `README-developers.md` (requirements roles, Tox how-to, contributor workflow); ignore Ruff/mypy/tool caches in `.gitignore`.

### 0.5.7

* Promote common PyWebView window knobs to first-class `glue.start()` kwargs (`frameless`, `easy_drag`, `shadow`, `debug`, `confirm_close`, `fullscreen` / `minimized` / `maximized` / `on_top`, `min_size`, `icon`, `gui`, `menu`). Explicit values win over the same key in `webview_options=`; unset (`None`) keeps prior Glue defaults. `webview_options` remains the escape hatch for the long tail.
* Default omitted window `size` is **1280×720** on every host (`_start_args` → Chrome/Edge `/glue.js` `resizeTo`; same value for PyWebView `create_window`).
* Examples rely on that default (removed shared `examples/common.py` `WINDOW_SIZE`).
* README: one `glue.start()` options table with **Source** (Glue / PyWebView / both) and **Hosts** columns.
* Require `pywebview>=6.0` (development and testing have been on 6.2.x).
* Mode name is `'webview'` only (`'pywebview'` removed).
* Server-only mode is `mode=None` only (`False` removed).

### 0.5.6

* Fix Windows `pip install` from GitHub: `setup.py` now reads the README as UTF-8 so install no longer fails on non-ASCII characters.

### 0.5.5

* Rename `webview.chrome_config()` → `webview.titlebar_config()` (in-page title bar payload for `glue.js`; avoids “Chrome browser” confusion).
* Clarify `mode='custom'`: `cmdline_args` is the full `Popen` argv, not extra browser flags (README + docstrings).
* README: Python→JS call queue waits for the **WebSocket**, distinct from the HTTP server being ready before the window opens.

### 0.5.4

* Rename `glue.chromium` → `glue.browsers_launcher` (shared Chrome/Edge launch + find helpers; avoids sounding like a third browser).
* Docs/hygiene: README quick-start path example, PyWebView default size note, `show()` docstring fixes, `python -m glue` description is PyWebView-first.
* Drop redundant integration `test_02` (harness forces `mode=None`, so it never tested Chrome).
* Presentation example uses `glue.start()` without redundant `'index.html'`.
* Remove leftover temp file under `examples/01 - hello_world/`.

### 0.5.3

* DRY: shared Windows `App Paths` lookup and macOS `.app` finder in `glue.browsers_launcher` (used by Chrome and Edge).
* DRY: `platform_name()` lives in `glue.browsers_launcher`; `glue.webview` imports it (single OS naming helper).
* DRY: in-page title-bar height comes only from the Python `_webview` payload — removed duplicate height map in `glue.js`.

### 0.5.2

* **Security:** Encode `_py_functions` in `/glue.js` with JSON (not Python `list` repr); validate every `@glue.expose` name as a JS identifier; raise `ValueError` on duplicate expose (no longer `assert`).
* **Security:** Python exceptions returned to the page include `errorText` only — full tracebacks stay on the server console.
* **Security:** When `all_interfaces` is false (default), reject Glue WebSocket clients whose peer is not loopback (`127.0.0.1` / `::1`).
* Example `05 - file_access` uses `textContent` instead of `innerHTML` for RPC results.
* README: short security note on the expose/localhost trust boundary.

### 0.5.1

* Rename internal modules: `glue.settings_store` → `glue.settings`, `glue.webview_host` → `glue.webview` (public API unchanged: `glue.settings()` / PyWebView host).
* Version bump only otherwise.

### 0.5.0

* **Breaking (default host):** `mode='auto'` prefers **PyWebView** on all platforms for a real desktop window, then falls back to Chrome/Chromium app mode, then Microsoft Edge on Windows only.
* `glue.start()` defaults to opening `index.html` when no page arguments are passed.
* Add optional `app_name=` on `glue.init()` with `glue.settings()` / `glue.save_settings()` / `glue.settings_path()` for user JSON under `~/.{app_name}/{app_name}.json` (opt-in; no files created until first save). Explicit paths work without `app_name`.
* Add explicit modes `'webview'` / `'pywebview'`; add `title` and `webview_options` on `glue.start()`, plus `glue.get_webview_windows()` for native window control.
* PyWebView is a runtime dependency (`pywebview>=5.0`) with graceful Chrome/Edge fallback if import or GUI startup fails. `block=False` with `auto` skips PyWebView (GUI loop must own the main thread).
* Run the Bottle/gevent server in an OS thread when PyWebView is used so the GUI loop does not starve the hub (blank/unresponsive windows).
* PyWebView defaults: no native app menus, frameless window, OS-styled in-page title bar (Windows / macOS / Linux) with working min/max/close via `webview_minimize` / `webview_toggle_maximize` / `webview_close`. Pass `webview_options={'frameless': False}` for native OS chrome.
* Add `resizable=` on `glue.start()` (default `True`) for PyWebView window resizing; override with `resizable=False` or `webview_options={'resizable': False}`.
* Frameless Windows: install edge/corner resize grips that drive native Win32 resize (`webview_start_resize`) — PyWebView alone does not resize frameless windows on Windows.
* Title bar shows `favicon.ico` (or `<link rel="icon">`) next to the title when present; PyWebView `icon=` is set from `ui/favicon.ico` when available.
* Frameless title bar is treated as non-client chrome: window height grows by the bar, content is inset (`padding-top`) so `size=` stays content pixels and the bar does not cover the UI.

### 0.4.0

* **Breaking:** Default frontend folder is `ui/` (was the `web/` convention). `glue.init()` now defaults to `path='ui'`; pass another path to override (e.g. CRA `build` / `src`).
* **Breaking:** `python -m glue` packaging CLI argument renamed from `web_folder` to `ui_folder`.
* Rename example frontend folders from `web/` to `ui/` and update docs/examples accordingly.

### 0.3.9

* Add `glue.__version__` (kept in sync with `setup.py`).
* Expand `examples/00 - presentation` into a 1920×1080 GSAP showcase: brand cover page-turn, scroll story, Windows/macOS/Linux window demos, and live parallel JS↔Python bridge demos.
* Examples serve `favicon.ico` from each example's own `web/` (or CRA `public/`) instead of shared Bottle routes from repo `assets/`.
* Modernize README around the presentation walkthrough (screenshot gallery paths under `assets/readme/`) and simplify the technical docs.

### 0.3.8

* Add `examples/11 - presentation`: 1080p brand showcase (logo, wordmark, slogan) for README screenshots.

### 0.3.7

* `mode='auto'` prefers Chrome/Chromium on all platforms; Edge is Windows-only fallback if Chrome is missing. macOS/Linux require Chrome/Chromium (no Edge fallback).

### 0.3.6

* Examples: shared favicon/branding from repo `assets/` via `examples/common.py` (no per-example `favicon.ico` copies); default window size `1280×720`.
* CRA keeps one favicon under `public/` (static build); window size aligned to `1280×720`.

### 0.3.5

* Docs: drop upstream Eel hero screenshot; fix default `allowed_extensions` (include `.vue`); renumber file_access example README; label pre-fork CHANGELOG history; refresh README-developers (webdriver_manager, GHA, pytest).
* Share Chromium launch path for Chrome/Edge (`glue/chromium.py`); drop bogus `win64` platform checks.
* Add unit tests for URL building, auto browser order, and `mode=None`/`False` / unsupported mode.

### 0.3.4

* Align packaging: `setup.py` declares gevent stack; `requirements.txt` matches and drops the `greenlet<2` pin (blocked modern Python).
* `pip install 'Glue[build]'` for PyInstaller; `python -m glue` uses `importlib.resources` and a clear error if PyInstaller is missing.
* Modernize GitHub Actions (`checkout`/`setup-python` v4/v5), CodeQL v3 (remove unsafe `HEAD^2` checkout), publish via `python -m build` + wheel.

### 0.3.3

* Protocol: unknown JS (and Python) exposed names return an error instead of hanging until timeout.
* Protocol: unify RPC error shape as `{errorText, errorTraceback}` both directions (legacy string+`stack` still accepted on Python receive).
* Protocol: await Promises returned from exposed JS functions before sending the result.
* Protocol: Python→JS calls go to the most recently connected page only (no multi-socket broadcast / return races).

### 0.3.2

* Fail startup if the webserver never becomes ready (no more silent browser open on a dead port).
* Replace `exec`-based JS stubs with `setattr` + strict identifier validation.
* Fix mutable default arguments on `init` / `start` (`allowed_extensions`, `cmdline_args`, `geometry`, `app`).
* Correct `geometry` typing (`WindowGeometryT` with size/position).
* Warn when `all_interfaces=True` (exposed functions reachable on the network).

### 0.3.1

* Fix unit `test_init` (was asserting `None == None` via `.sort()`).
* Fix sync-callbacks integration assertion to require `sync_callbacks.html`.
* Fix integration test harness so `mode=None` / `port=0` actually override example `glue.start()` defaults, and port discovery checks the parent process (not only children).
* Harden hello-world console assertions against unrelated browser noise (e.g. missing favicon 404).
* Remove dead `suppress_error` / `api_error_message`, unused `future` dependency, Py2-era imports.
* Remove Electron leftover shim and `debugger` from `glue.js`.
* Delete obsolete `.travis.yml`; update FUNDING and issue templates for Glue / Chromium-family.
* Doc scrub: Eel leftovers in docstrings/CLI; README `js_result_timeout` name.

### 0.3.0

* Start the webserver before opening the browser and wait until the port accepts connections (fixes early load / race crashes that previously required a post-install Eel patch).

### 0.2.0

* Default browser mode is now `'auto'`: Edge then Chrome on Windows; Chrome/Chromium elsewhere (always app mode by default).
* Dropped Electron, MSIE, and system-default `webbrowser` fallback. Supported modes: `auto`, `chrome`, `edge`, `custom`, `None`/`False`.
* Hardened Edge launcher to resolve `msedge.exe` and launch without `shell=True`.
* Removed Electron and Edge-only example folders (default auto covers Windows Edge).

### 0.1.0

* Rebrand fork as **Glue** (`import glue`, `/glue.js`, `/glue` WebSocket).
* Courtesy attribution to upstream [Eel](https://github.com/python-eel/Eel).
* Package metadata points at https://github.com/alepodj/Glue

---

## Upstream Eel history (pre-fork)

Entries below are from [python-eel/Eel](https://github.com/python-eel/Eel) before the Glue fork. Some mention Electron, MSIE, or older APIs that **Glue 0.2.0+ no longer supports**.

### 0.18.2

* Switch from using `pkg_resources` to `importlib.resources`: https://github.com/python-eel/Eel/pull/766

### 0.18.1

* Fix: Include `typing_extensions` in install requirements.

### 0.18.0
* Added support for MS Internet Explorer in #744.
* Added supported for app_mode in the Edge browser in #744.
* Improved type annotations in #683.

### 0.17.0
* Adds support for Python 3.11 and Python 3.12

### v0.16.0
* Drop support for Python versions below 3.7

### v0.15.3
* Comprehensive type hints implement by @thatfloflo in https://github.com/python-eel/Eel/pull/577.

### v0.15.2
* Adds `register_glue_routes` to handle applying Eel routes to non-Bottle custom app instances.

### v0.15.1
* Bump bottle dependency from 0.12.13 to 0.12.20 to address the critical CVE-2022-31799 and moderate CVE-2020-28473.

### v0.15.0
* Add `shutdown_delay` as a `start()` function parameter ([#529](https://github.com/python-eel/Eel/pull/529))

### v0.14.0
* Change JS function name parsing to use PyParsing rather than regex, courtesy @KyleKing.

### v0.13.2
* Add `default_path` start arg to define a default file to retrieve when hitting the root URL.

### v0.13.1
* Shut down the Eel server less aggressively when websockets get closed (#337)

## v0.13.0
* Drop support for Python versions below 3.6
* Add `jinja2` as an extra for pip installation, e.g. `pip install glue[jinja2]`.
* Bump dependencies in examples to dismiss github security notices. We probably want to set up a policy to ignore example dependencies as they shouldn't be considered a source of vulnerabilities.
* Disable edge on non-Windows platforms until we implement proper support.

### v0.12.4
* Return greenlet task from `spawn()` ([#300](https://github.com/samuelhwilliams/Eel/pull/300))
* Set JS mimetype to reduce errors on Windows platform ([#289](https://github.com/samuelhwilliams/Eel/pull/289))

### v0.12.3
* Search for Chromium on macOS.

### v0.12.2
* Fix a bug that prevents using middleware via a custom Bottle.

### v0.12.1
* Check that Chrome path is a file that exists on Windows before blindly returning it.

## v0.12.0
* Allow users to override the amount of time Python will wait for Javascript functions running via Eel to run before bailing and returning None.

### v0.11.1
* Fix the implementation of #203, allowing users to pass their own bottle instances into Eel.

## v0.11.0
* Added support for `app` parameter to `glue.start`, which will override the bottle app instance used to run eel. This
allows developers to apply any middleware they wish to before handing over to eel.
* Disable page caching by default via new `disable_cache` parameter to `glue.start`.
* Add support for listening on all network interfaces via new `all_interfaces` parameter to `glue.start`.
* Support for Microsoft Edge

### v0.10.4
* Fix PyPi project description.

### v0.10.3
* Fix a bug that prevented using Eel without Jinja templating.

### v0.10.2
* Only render templates from within the declared jinja template directory.

### v0.10.1
* Avoid name collisions when using Electron, so jQuery etc work normally

## v0.10.0
* Corrective version bump after new feature included in 0.9.13
* Fix a bug with example 06 for Jinja templating; the `templates` kwarg to `glue.start` takes a filepath, not a bool.

### v0.9.13
* Add support for Jinja templating.

### Earlier
* No changelog notes for earlier versions.
