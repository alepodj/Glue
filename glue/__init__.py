from __future__ import annotations

import atexit
import json as jsn
import traceback
import warnings
from collections.abc import Callable
from typing import Any

import bottle as btl
import gevent as gvt

from glue.types import OptionsDictT, WebSocketT, WindowGeometryT

try:
    import bottle_websocket as wbs
except ImportError:
    import bottle.ext.websocket as wbs
import mimetypes
import os
import random as rnd
import re as rgx
import socket
import sys
import threading
import time
from importlib.resources import as_file, files

import pyparsing as pp

import glue.browsers as brw
import glue.settings as _settings
import glue.splash as _splash

__version__ = '0.6.7'


mimetypes.add_type('application/javascript', '.js')

_glue_js_reference = files('glue') / 'glue.js'
with as_file(_glue_js_reference) as _glue_js_path:
    _glue_js: str = _glue_js_path.read_text(encoding='utf-8')

_websockets: list[tuple[Any, WebSocketT]] = []
_call_return_values: dict[Any, Any] = {}
_call_return_callbacks: dict[float, tuple[Callable[..., Any], Callable[..., Any] | None]] = {}
_call_number: int = 0
_exposed_functions: dict[Any, Any] = {}
_js_functions: list[Any] = []
_mock_queue: list[Any] = []
_mock_queue_done: set[Any] = set()
_shutdown: gvt.Greenlet | None = None  # Later assigned as global by _websocket_close()
root_path: str  # Later assigned as global by init()

# The maximum time (in milliseconds) that Python will try to retrieve a return value for functions executing in JS
# Can be overridden through `glue.init` with the kwarg `js_result_timeout` (default: 10000)
_js_result_timeout: int = 10000

# Attribute holding the start args from calls to glue.start()
_start_args: OptionsDictT = {}
_splash_session: _splash.SplashController | None = None
_splash_pages: set[str] = set()


def _merge_webview_options(base: dict[str, Any] | None, **first_class: Any) -> dict[str, Any]:
    """Merge escape-hatch dict with first-class kwargs (explicit values win)."""
    merged = dict(base or {})
    for key, value in first_class.items():
        if value is not None:
            merged[key] = value
    return merged


def _close_splash() -> None:
    global _splash_session
    session, _splash_session = _splash_session, None
    if session is not None:
        session.close()


def _dismiss_splash(page: str | None = None) -> None:
    session = _splash_session
    if session is None:
        return
    normalized = (page or '').lstrip('/')
    if page is None or not _splash_pages or normalized in _splash_pages:
        session.dismiss()


def _resolve_centered(
    centered: bool | None,
    splash: bool | str | os.PathLike[str],
    position: tuple[int, int] | None,
) -> bool:
    if centered is not None and not isinstance(centered, bool):
        raise TypeError("'centered' must be True, False, or None")
    if centered is None:
        return splash is not False and position is None
    if centered and position is not None:
        raise ValueError("'centered=True' cannot be combined with 'position'")
    return centered


atexit.register(_close_splash)


_DEFAULT_ALLOWED_EXTENSIONS: list[str] = ['.js', '.html', '.txt', '.htm', '.xhtml', '.vue']
_DEFAULT_CMDLINE_ARGS: list[str] = ['--disable-http-cache']
_JS_NAME_RE = rgx.compile(r'^[A-Za-z_][A-Za-z0-9_]*$')
_this_module = sys.modules[__name__]


# Public functions


def expose(name_or_function: Callable[..., Any] | None = None) -> Callable[..., Any]:
    """Decorator to expose Python callables via Glue's JavaScript API.

    When an exposed function is called, a callback function can be passed
    immediately afterwards. This callback will be called asynchronously with
    the return value (possibly `None`) when the Python function has finished
    executing.

    Blocking calls to the exposed function from the JavaScript side are only
    possible using the :code:`await` keyword inside an :code:`async function`.
    These still have to make a call to the response, i.e.
    :code:`await glue.py_random()();` inside an :code:`async function` will work,
    but just :code:`await glue.py_random();` will not.

    :Example:

    In Python do:

    .. code-block:: python

        @expose
        def say_hello_py(name: str = 'You') -> None:
            print(f'{name} said hello from the JavaScript world!')

    In JavaScript do:

    .. code-block:: javascript

        glue.say_hello_py('Alice')();

    Expected output on the Python console::

        Alice said hello from the JavaScript world!

    """
    # Deal with '@glue.expose()' - treat as '@glue.expose'
    if name_or_function is None:
        return expose

    if isinstance(name_or_function, str):  # Called as '@glue.expose("my_name")'
        name = name_or_function

        def decorator(function: Callable[..., Any]) -> Any:
            _expose(name, function)
            return function

        return decorator
    else:
        function = name_or_function
        _expose(function.__name__, function)
        return function


# PyParsing grammar for parsing exposed functions in JavaScript code
# Examples: `glue.expose(w, "func_name")`, `glue.expose(func_name)`, `glue.expose((function (e){}), "func_name")`
EXPOSED_JS_FUNCTIONS: pp.ZeroOrMore = pp.ZeroOrMore(
    pp.Suppress(
        pp.SkipTo(pp.Literal('glue.expose('))
        + pp.Literal('glue.expose(')
        + pp.Optional(
            pp.Or([pp.nested_expr(), pp.Word(pp.printables, exclude_chars=',')]) + pp.Literal(',')
        )
    )
    + pp.Suppress(pp.Regex(r'["\']?'))
    + pp.Word(pp.printables, exclude_chars='"\')')
    + pp.Suppress(pp.Regex(r'["\']?\s*\)')),
)


def init(
    path: str = 'ui',
    allowed_extensions: list[str] | None = None,
    js_result_timeout: int = 10000,
    app_name: str | None = None,
) -> None:
    """Initialise Glue.

    This function should be called before :func:`start()` to initialise the
    parameters for the web interface, such as the path to the files to be
    served.

    :param path: Sets the path on the filesystem where files to be served to
        the browser are located. *Default:* :file:`ui`.
    :param allowed_extensions: A list of filename extensions which will be
        parsed for exposed glue functions which should be callable from python.
        Files with extensions not in *allowed_extensions* will still be served,
        but any JavaScript functions, even if marked as exposed, will not be
        accessible from python.
        *Default:* :code:`['.js', '.html', '.txt', '.htm', '.xhtml', '.vue']`.
    :param js_result_timeout: How long Glue should be waiting to register the
        results from a call to Glue's JavaScript API before before timing out.
        *Default:* :code:`10000` milliseconds.
    :param app_name: Optional. When set, unlocks the default user settings
        path :file:`~/.{app_name}/{app_name}.json` for :func:`settings` /
        :func:`save_settings`. Does not create any files. *Default:* `None`.
    """
    global root_path, _js_functions, _js_result_timeout
    root_path = _get_real_path(path)

    if allowed_extensions is None:
        allowed_extensions = list(_DEFAULT_ALLOWED_EXTENSIONS)

    js_functions = set()
    for root, _, filenames in os.walk(root_path):
        for name in filenames:
            if not any(name.endswith(ext) for ext in allowed_extensions):
                continue

            try:
                with open(os.path.join(root, name), encoding='utf-8') as file:
                    contents = file.read()
                    expose_calls = set()
                    matches = EXPOSED_JS_FUNCTIONS.parse_string(contents).as_list()
                    for expose_call in matches:
                        expose_calls.add(_validate_js_name(expose_call))
                    js_functions.update(expose_calls)
            except UnicodeDecodeError:
                pass  # Malformed file probably

    _js_functions = list(js_functions)
    for js_function in _js_functions:
        _mock_js_function(js_function)

    _js_result_timeout = js_result_timeout
    _settings.configure(app_name)


def settings(path: str | None = None) -> dict[str, Any]:
    """Load app settings JSON as a plain dict.

    With no *path*, uses :file:`~/.{app_name}/{app_name}.json` (requires
    :code:`app_name` on :func:`init`). Missing file returns :code:`{}` and
    does not create anything on disk. Pass an explicit *path* to load any
    JSON file (works without :code:`app_name`).

    Mutate the dict as usual, then :func:`save_settings` to persist.
    """
    return _settings.load(path)


def save_settings(data: dict[str, Any], path: str | None = None) -> str:
    """Write settings dict as JSON. Creates parent directories on first save.

    With no *path*, writes to the last path used by :func:`settings`, or the
    default path when :code:`app_name` is set. Returns the path written.
    """
    return str(_settings.save(data, path))


def settings_path() -> str:
    """Return the default settings file path (requires :code:`app_name`)."""
    return str(_settings.settings_path())


def start(
    *start_urls: str,
    mode: str | None = 'auto',
    host: str = 'localhost',
    port: int = 8000,
    block: bool = True,
    jinja_templates: str | None = None,
    cmdline_args: list[str] | None = None,
    size: tuple[int, int] | None = None,
    position: tuple[int, int] | None = None,
    centered: bool | None = None,
    geometry: dict[str, WindowGeometryT] | None = None,
    close_callback: Callable[..., Any] | None = None,
    app_mode: bool = True,
    all_interfaces: bool = False,
    disable_cache: bool = True,
    default_path: str = 'index.html',
    app: btl.Bottle | None = None,
    shutdown_delay: float = 1.0,
    title: str | None = None,
    resizable: bool = True,
    frameless: bool | None = None,
    easy_drag: bool | None = None,
    shadow: bool | None = None,
    debug: bool | None = None,
    confirm_close: bool | None = None,
    fullscreen: bool | None = None,
    minimized: bool | None = None,
    maximized: bool | None = None,
    on_top: bool | None = None,
    min_size: tuple[int, int] | None = None,
    icon: str | None = None,
    gui: str | None = None,
    menu: list[Any] | None = None,
    webview_options: dict[str, Any] | None = None,
    splash: bool | str | os.PathLike[str] = False,
    splash_min_duration: int | float = 1.0,
) -> None:
    """Start the Glue app.

    Suppose you put all the frontend files in a directory called
    :file:`ui`, including your start page :file:`index.html`, then the app
    is started like this:

    .. code-block:: python

        import glue
        glue.init()
        glue.start()

    This will start a webserver on the default settings
    (http://localhost:8000) and open a native window (or browser) to
    http://localhost:8000/index.html. Pass one or more page paths to open
    something else, e.g. :code:`glue.start('main.html')`.

    By default (:code:`mode='auto'`), Glue prefers **PyWebView** for a real
    desktop window (menus, minimize/maximize/close under your control), then
    falls back to Chrome/Chromium in app mode, then Microsoft Edge on Windows
    only. Use :code:`block=False` with :code:`mode='auto'` to skip PyWebView
    (its GUI loop must own the main thread) and launch Chrome/Edge instead.

    :param start_urls: One or more relative page paths to open. *Default:*
        :code:`('index.html',)`.
    :param mode: Window host selection. :code:`'auto'` (default) tries
        PyWebView, then Chrome/Chromium, then Edge on Windows. Force
        :code:`'webview'`, :code:`'chrome'`, or
        :code:`'edge'`; use :code:`'custom'` with :code:`cmdline_args` as a
        full :func:`subprocess.Popen` argv list; or :code:`None` for no window.
    :param host: Hostname used for Bottle server. *Default:*
        :code:`'localhost'`.
    :param port: Port used for Bottle server. Use :code:`0` for port to be
        picked automatically. *Default:* :code:`8000`.
    :param block: Whether the call to :func:`start()` blocks the calling
        thread. *Default:* `True`. PyWebView requires :code:`True` when used
        as the window host.
    :param jinja_templates: Folder for :mod:`jinja2` templates, e.g.
        :file:`my_templates`. *Default:* `None`.
    :param cmdline_args: Extra flags for Chrome/Edge (appended to the browser
        command). With :code:`mode='custom'`, this is the **full** argv passed
        to :func:`subprocess.Popen` (executable + args). Example for Chrome:
        :code:`glue.start('main.html', mode='chrome', port=8080,
        cmdline_args=['--start-fullscreen', '--browser-startup-dialog'])`.
        *Default:* :code:`['--disable-http-cache']`.
    :param size: Tuple specifying the (width, height) of the main window in
        pixels. Applied on PyWebView via window kwargs and on Chrome/Edge via
        :code:`window.resizeTo` in :file:`/glue.js`. *Default:* `None`
        (Glue uses :code:`(1280, 720)`).
    :param position: Tuple specifying the (left, top) position of the main
        window in pixels. Chrome/Edge use :code:`window.moveTo` in
        :file:`/glue.js`. *Default*: `None` (host chooses, usually centered).
    :param centered: Explicitly center the main window. Supported by PyWebView,
        Chrome, and Edge. :code:`None` automatically enables centering when
        :code:`splash` is enabled; :code:`False` opts out. Per-page
        :code:`geometry` positions override centering. Explicit :code:`True`
        cannot be combined with global :code:`position`. On Windows PyWebView
        this uses the primary work area; Chrome/Edge and other platforms use
        available-screen geometry or host placement. *Default:* :code:`None`.
    :param geometry: Per-page size/position map (page path →
        :code:`{'size': (w, h), 'position': (x, y)}`, either key optional).
        Applied on PyWebView and via :file:`/glue.js` for Chrome/Edge.
        *Default:* :code:`{}`.
    :param close_callback: A lambda or function that is called when a websocket
        or window closes (i.e. when the user closes the window). It should take
        two arguments: a string which is the relative path of the page that
        just closed, and a list of the other websockets that are still open.
        *Default:* `None`.
    :param app_mode: Whether to run Edge/Chrome in App Mode (:code:`--app`).
        *Default:* :code:`True`. Ignored for PyWebView.
    :param all_interfaces: Whether to allow the :mod:`bottle` server to listen
        for connections on all interfaces (:code:`0.0.0.0`) and accept Glue
        WebSocket clients from non-loopback peers. **Warning:** any client that
        can reach this host can invoke every :func:`expose`d Python function
        over the WebSocket. Use only on trusted networks. When :code:`False`
        (default), non-loopback WebSocket peers are rejected. *Default:*
        :code:`False`.
    :param disable_cache: Sets the no-store response header when serving
        assets.
    :param default_path: The default file to retrieve for the root URL.
    :param app: An instance of :class:`bottle.Bottle` which will be used rather
        than creating a fresh one. This can be used to install middleware on
        the instance before starting Glue, e.g. for session management,
        authentication, etc. If *app* is not a :class:`bottle.Bottle` instance,
        you will need to call :code:`glue.register_glue_routes(app)` on your
        custom app instance.
    :param shutdown_delay: Timer configurable for Glue's shutdown detection
        mechanism, whereby when any websocket closes, it waits *shutdown_delay*
        seconds, and then checks if there are now any websocket connections.
        If not, then Glue closes. In case the user has closed the browser and
        wants to exit the program. *Default:* :code:`1.0` seconds.
    :param title: Window title. Applied to PyWebView's native/in-page chrome
        and, when set, to ``document.title`` via :file:`/glue.js` so Chrome/Edge
        app-mode captions match. When omitted, Chrome/Edge keep each page's
        ``<title>``. *Default:* :code:`None` (PyWebView falls back to
        :code:`'Glue'`).
    :param resizable: Whether the user can resize the window (PyWebView).
        *Default:* :code:`True`. Ignored for Chrome/Edge app windows unless
        you pass matching browser flags yourself.
    :param frameless: PyWebView: hide native caption bar (Glue draws an
        in-page title bar). *Default when unset:* :code:`True`.
    :param easy_drag: PyWebView: drag window from anywhere when frameless.
        *Default when unset:* :code:`False` (drag via title-bar region).
    :param shadow: PyWebView window shadow (Windows). *Default when unset:*
        :code:`True` on Windows.
    :param debug: PyWebView: DevTools / browser accelerators. *Default when
        unset:* :code:`False`.
    :param confirm_close: PyWebView: native close confirmation. *Default when
        unset:* :code:`False`.
    :param fullscreen: PyWebView start fullscreen. *Default when unset:*
        :code:`False`.
    :param minimized: PyWebView start minimized. *Default when unset:*
        :code:`False`.
    :param maximized: PyWebView start maximized. *Default when unset:*
        :code:`False`.
    :param on_top: PyWebView always-on-top. *Default when unset:* :code:`False`.
    :param min_size: PyWebView ``(width, height)`` minimum. *Default when
        unset:* :code:`(200, 100)`.
    :param icon: Path to ``.ico`` (Windows) / ``.icns`` (macOS) for the native
        window. *Default when unset:* ``ui/favicon.ico`` if present.
    :param gui: Force PyWebView backend (``edgechromium``, ``qt``, ``gtk``,
        …). *Default when unset:* auto.
    :param menu: PyWebView application :class:`Menu` list. *Default when
        unset:* no menus (``[]``).
    :param webview_options: Escape hatch for other PyWebView
        :func:`webview.create_window` / :func:`webview.start` kwargs (e.g.
        :code:`private_mode`, :code:`transparent`). Explicit first-class
        kwargs above win over the same key here. *Default:* :code:`None`.
    :param splash: Show a transparent GLFW splash while Glue starts. Pass
        :code:`True` to discover a PNG/APNG/GIF named ``splash`` in the UI
        folder or project root, or pass an explicit image path. Requires the
        optional ``glue-ui[splash]`` extra. *Default:* :code:`False`.
    :param splash_min_duration: Minimum number of seconds the splash remains
        visible, even when the page becomes ready sooner. Use :code:`0` to
        disable the minimum. *Default:* :code:`1.0`.
    """
    global _splash_pages, _splash_session
    splash_min_duration = _splash.validate_min_duration(splash_min_duration)
    centered = _resolve_centered(centered, splash, position)
    if cmdline_args is None:
        cmdline_args = list(_DEFAULT_CMDLINE_ARGS)
    if geometry is None:
        geometry = {}
    webview_options = _merge_webview_options(
        webview_options,
        frameless=frameless,
        easy_drag=easy_drag,
        shadow=shadow,
        debug=debug,
        confirm_close=confirm_close,
        fullscreen=fullscreen,
        minimized=minimized,
        maximized=maximized,
        on_top=on_top,
        min_size=min_size,
        icon=icon,
        gui=gui,
        menu=menu,
    )
    if app is None:
        app = btl.default_app()
    if not start_urls:
        start_urls = ('index.html',)

    if all_interfaces:
        warnings.warn(
            'all_interfaces=True binds on 0.0.0.0 and allows non-loopback '
            'Glue WebSocket clients; any client that can reach this host can '
            'call @glue.expose Python functions. Use only on trusted networks.',
            UserWarning,
            stacklevel=2,
        )

    # Omit / None → DEFAULT_WINDOW_SIZE (Chrome/Edge resizeTo + PyWebView create_window).
    if size is None:
        import glue.webview as webview

        size = webview.DEFAULT_WINDOW_SIZE

    _start_args.update(
        {
            'mode': mode,
            'host': host,
            'port': port,
            'block': block,
            'jinja_templates': jinja_templates,
            'cmdline_args': cmdline_args,
            'size': size,
            'position': position,
            'centered': centered,
            'geometry': geometry,
            'title': title,
            'resizable': resizable,
            'webview_options': webview_options,
            'close_callback': close_callback,
            'app_mode': app_mode,
            'all_interfaces': all_interfaces,
            'disable_cache': disable_cache,
            'default_path': default_path,
            'app': app,
            'shutdown_delay': shutdown_delay,
            'splash': splash,
            'splash_min_duration': splash_min_duration,
        }
    )

    if _start_args['port'] == 0:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(('localhost', 0))
        _start_args['port'] = sock.getsockname()[1]
        sock.close()

    if _start_args['jinja_templates'] is not None:
        from jinja2 import Environment, FileSystemLoader, select_autoescape

        if not isinstance(_start_args['jinja_templates'], str):
            raise TypeError("'jinja_templates' start_arg/option must be of type str")
        templates_path = os.path.join(root_path, _start_args['jinja_templates'])
        _start_args['jinja_env'] = Environment(
            loader=FileSystemLoader(templates_path), autoescape=select_autoescape(['html', 'xml'])
        )

    # verify shutdown_delay is correct value
    if not isinstance(_start_args['shutdown_delay'], (int, float)):
        raise ValueError(
            '`shutdown_delay` must be a number, got a {}'.format(
                type(_start_args['shutdown_delay'])
            )
        )

    def run_lambda() -> None:
        if _start_args['all_interfaces'] is True:
            HOST = '0.0.0.0'
        else:
            if not isinstance(_start_args['host'], str):
                raise TypeError("'host' start_arg/option must be of type str")
            HOST = _start_args['host']

        app = _start_args['app']

        if isinstance(app, btl.Bottle):
            register_glue_routes(app)
        else:
            register_glue_routes(btl.default_app())

        btl.run(
            host=HOST,
            port=_start_args['port'],
            server=wbs.GeventWebSocketServer,
            quiet=True,
            app=app,
        )  # Always returns None

    def _wait_for_server(*, cooperative: bool = True) -> None:
        """Wait until the server is accepting connections, then open the window.

        When the Bottle server runs as a gevent greenlet on this hub, use
        cooperative :func:`gevent.sleep` so the server can accept during the
        wait. When it runs in another OS thread (PyWebView), use
        :func:`time.sleep` so we do not depend on this thread's hub.
        """
        sleep = gvt.sleep if cooperative else time.sleep
        host = _start_args['host'] if not _start_args['all_interfaces'] else '127.0.0.1'
        if not isinstance(host, str):
            host = '127.0.0.1'
        # Bottle on 0.0.0.0 is reached via loopback for the readiness probe
        if host in ('0.0.0.0', '::'):
            host = '127.0.0.1'
        port = _start_args['port']
        if not isinstance(port, int):
            raise TypeError("'port' start_arg/option must be of type int")
        ready = False
        for _ in range(100):
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(0.2)
                sock.connect((host, port))
                sock.close()
                ready = True
                break
            except OSError:
                sleep(0.05)
        if not ready:
            raise RuntimeError(
                'Glue server did not become ready on %s:%s '
                '(not accepting connections after startup wait)' % (host, port)
            )
        show(*start_urls)

    def _should_run_server_in_thread() -> bool:
        """PyWebView blocks the main thread; a gevent server greenlet would starve."""
        mode = _start_args.get('mode')
        if mode in brw.WEBVIEW_MODES:
            return bool(_start_args.get('block', True))
        if mode == 'auto':
            import glue.webview as webview

            return webview.should_try(_start_args)
        return False

    _close_splash()
    _splash_pages = {str(page).lstrip('/') for page in start_urls}
    if splash is not False and mode is not None:
        _splash_session = _splash.start_splash(
            splash,
            ui_root=root_path,
            project_root=_get_real_path('.'),
            min_duration=splash_min_duration,
        )

    # Start the webserver first, then open the window once listening (avoids race).
    # PyWebView's GUI loop blocks the main thread, so the Bottle server must run
    # in a real OS thread in that case — not a greenlet on the same hub.
    try:
        if _should_run_server_in_thread():
            server_thread = threading.Thread(target=run_lambda, name='glue-bottle', daemon=True)
            server_thread.start()
            _wait_for_server(cooperative=False)
            # GUI closed: exit so we do not hang joining a daemon server thread.
            if brw.webview_session_completed():
                _close_splash()
                sys.exit(0)
            if _start_args['block']:
                # PyWebView failed over to Chrome/Edge; wait until websockets exit.
                server_thread.join()
        else:
            server_greenlet = spawn(run_lambda)
            _wait_for_server(cooperative=True)
            if brw.webview_session_completed():
                _close_splash()
                sys.exit(0)
            if _start_args['block']:
                server_greenlet.join()
    except BaseException:
        _close_splash()
        raise


def get_webview_windows() -> list[Any]:
    """Return PyWebView window instances for the current Glue session.

    Empty when Chrome/Edge (or no window) is used. Useful for menus, title,
    and other native window control via the PyWebView API.
    """
    import glue.webview as webview

    return webview.get_windows()


def show(*start_urls: str) -> None:
    """Show the specified URL(s) in the browser.

    Suppose you have two files in your :file:`ui` folder. The file
    :file:`hello.html` regularly includes :file:`glue.js` and provides
    interactivity, and the file     :file:`goodbye.html` does not include
    :file:`glue.js` and simply provides plain HTML content not reliant on Glue.

    First, we define a callback function to be called when the browser
    window is closed:

    .. code-block:: python

        def last_calls():
           glue.show('goodbye.html')

    Now we initialise and start Glue, with a :code:`close_callback` to our
    function:

    .. code-block:: python

        glue.init()
        glue.start('hello.html', mode='auto', close_callback=last_calls)

    When the websocket from :file:`hello.html` is closed (e.g. because the
    user closed the browser window), Glue will wait *shutdown_delay* seconds
    (by default 1 second), then call our :code:`last_calls()` function, which
    opens another window with the :file:`goodbye.html` shown before our Glue app
    terminates.

    :param start_urls: One or more URLs to be opened.
    """
    brw.open(list(start_urls), _start_args)


def sleep(seconds: int | float) -> None:
    """A non-blocking sleep call compatible with the Gevent event loop.

    .. note::
        While this function simply wraps :func:`gevent.sleep()`, it is better
        to call :func:`glue.sleep()` in your Glue app, as this will ensure future
        compatibility in case the implementation of Glue should change in some
        respect.

    :param seconds: The number of seconds to sleep.
    """
    gvt.sleep(seconds)


def spawn(function: Callable[..., Any], *args: Any, **kwargs: Any) -> gvt.Greenlet:
    """Spawn a new Greenlet.

    Calling this function will spawn a new :class:`gevent.Greenlet` running
    *function* asynchronously.

    .. caution::
        If you spawn your own Greenlets to run in addition to those spawned by
        Glue's internal core functionality, you will have to ensure that those
        Greenlets will terminate as appropriate (either by returning or by
        being killed via Gevent's kill mechanism), otherwise your app may not
        terminate correctly when Glue itself terminates.

    :param function: The function to be called and run as the Greenlet.
    :param *args: Any positional arguments that should be passed to *function*.
    :param **kwargs: Any key-word arguments that should be passed to
        *function*.
    """
    return gvt.spawn(function, *args, **kwargs)


# Bottle Routes


def _favicon_href() -> str | None:
    """URL for ``ui/favicon.ico`` with mtime cache-bust (Chrome favicon DB ignores Cache-Control)."""
    import glue.webview as webview

    path = webview._default_favicon_path()
    if not path:
        return None
    try:
        version = int(os.path.getmtime(path))
    except OSError:
        version = 0
    return '/favicon.ico?v=%d' % version


_ICON_LINK_RE = rgx.compile(
    r'<link\b[^>]*\brel\s*=\s*["\'](?:shortcut\s+)?icon["\']',
    rgx.IGNORECASE,
)
_HEAD_RE = rgx.compile(r'<head\b[^>]*>', rgx.IGNORECASE)


def _inject_html_favicon(html: str) -> str:
    """Insert a favicon ``<link>`` after ``<head>`` when ``ui/favicon.ico`` exists.

    Chromium ``--app`` windows read the icon from the first HTML document. Doing
    this server-side (not in ``glue.js``) puts the tag in the bytes before render.
    """
    href = _favicon_href()
    if not href or _ICON_LINK_RE.search(html):
        return html
    match = _HEAD_RE.search(html)
    if not match:
        return html
    link = '<link rel="icon" type="image/x-icon" href="%s">' % href
    return html[: match.end()] + '\n    ' + link + html[match.end() :]


def _response_body_text(response: btl.Response) -> str | None:
    """Best-effort decode of a Bottle response body as text."""
    body = getattr(response, 'body', None)
    if body is None:
        return None
    if isinstance(body, str):
        return body
    if isinstance(body, bytes):
        try:
            return body.decode('utf-8')
        except UnicodeDecodeError:
            return None
    read = getattr(body, 'read', None)
    if callable(read):
        data = read()
        if isinstance(data, str):
            return data
        if isinstance(data, bytes):
            try:
                return data.decode('utf-8')
            except UnicodeDecodeError:
                return None
    return None


def _maybe_inject_favicon_html(path: str, response: btl.Response) -> btl.Response:
    """Rewrite HTML responses to include ``/favicon.ico`` when present on disk."""
    lower = path.lower().split('?', 1)[0]
    if not (lower.endswith('.html') or lower.endswith('.htm')):
        return response
    status = getattr(response, 'status_code', None)
    if status is None:
        status = int(str(getattr(response, 'status', '200')).split()[0])
    if int(status) >= 400:
        return response
    text = _response_body_text(response)
    if text is None:
        return response
    # Always rebuild: static_file bodies are file-like and consumed by the read above.
    injected = _inject_html_favicon(text)
    out = btl.HTTPResponse(injected, status=status)
    content_type = response.get_header('Content-Type') or 'text/html; charset=UTF-8'
    out.set_header('Content-Type', content_type)
    for name, value in response.headers.items():
        if name.lower() in ('content-type', 'content-length'):
            continue
        out.set_header(name, value)
    return out


def _glue() -> str:
    import glue.webview as webview

    start_geometry = {
        'default': {
            'size': _start_args['size'],
            'position': _start_args['position'],
            'centered': _start_args.get('centered', False),
        },
        'pages': _start_args['geometry'],
    }

    page = _glue_js.replace(
        '/** _py_functions **/', '_py_functions: %s,' % _safe_json(list(_exposed_functions.keys()))
    )
    page = page.replace(
        '/** _start_geometry **/', '_start_geometry: %s,' % _safe_json(start_geometry)
    )
    page = page.replace('/** _webview **/', '_webview: %s,' % _safe_json(webview.titlebar_config()))
    window_title = _start_args.get('title')
    if not isinstance(window_title, str) or not window_title.strip():
        window_title = None
    else:
        window_title = window_title.strip()
    page = page.replace('/** _window_title **/', '_window_title: %s,' % _safe_json(window_title))
    page = page.replace('/** _favicon_href **/', '_favicon_href: %s,' % _safe_json(_favicon_href()))
    btl.response.content_type = 'application/javascript'
    _set_response_headers(btl.response)
    return page


def _root() -> btl.Response:
    if not isinstance(_start_args['default_path'], str):
        raise TypeError("'default_path' start_arg/option must be of type str")
    return _static(_start_args['default_path'])


def _static(path: str) -> btl.Response:
    response = None
    if 'jinja_env' in _start_args and 'jinja_templates' in _start_args:
        if not isinstance(_start_args['jinja_templates'], str):
            raise TypeError("'jinja_templates' start_arg/option must be of type str")
        template_prefix = _start_args['jinja_templates'] + '/'
        if path.startswith(template_prefix):
            n = len(template_prefix)
            template = _start_args['jinja_env'].get_template(path[n:])
            response = btl.HTTPResponse(template.render())

    if response is None:
        response = btl.static_file(path, root=root_path)

    response = _maybe_inject_favicon_html(path, response)
    _set_response_headers(response)
    return response


def _is_loopback_addr(addr: str | None) -> bool:
    """True if *addr* is a loopback client address (IPv4/IPv6 / mapped)."""
    if not addr:
        return False
    a = addr.strip().lower()
    if a in ('127.0.0.1', '::1', 'localhost'):
        return True
    return bool(a.startswith('::ffff:') and a.rsplit(':', 1)[-1] == '127.0.0.1')


def _websocket(ws: WebSocketT) -> None:
    global _websockets

    # Default: only loopback may open the Glue bridge (remote needs all_interfaces=True).
    if not _start_args.get('all_interfaces'):
        peer = btl.request.environ.get('REMOTE_ADDR')
        if not _is_loopback_addr(peer if isinstance(peer, str) else None):
            try:
                ws.close()
            except Exception:
                pass
            return

    for js_function in _js_functions:
        _import_js_function(js_function)

    page = btl.request.query.page
    if page not in _mock_queue_done:
        for call in _mock_queue:
            _repeated_send(ws, _safe_json(call))
        _mock_queue_done.add(page)

    _websockets += [(page, ws)]

    while True:
        msg = ws.receive()
        if msg is not None:
            message = jsn.loads(msg)
            if message.get('event') == 'page-ready':
                _dismiss_splash(page)
            else:
                spawn(_process_message, message, ws)
        else:
            _websockets.remove((page, ws))
            break

    _websocket_close(page)


BOTTLE_ROUTES: dict[str, tuple[Callable[..., Any], dict[Any, Any]]] = {
    '/glue.js': (_glue, dict()),
    '/': (_root, dict()),
    '/<path:path>': (_static, dict()),
    '/glue': (_websocket, dict(apply=[wbs.websocket])),
}


def register_glue_routes(app: btl.Bottle) -> None:
    """Register the required Glue routes with `app`.

    .. note::

        :func:`glue.register_glue_routes()` is normally invoked implicitly by
        :func:`glue.start()` and does not need to be called explicitly in most
        cases. Registering the Glue routes explicitly is only needed if you are
        passing something other than an instance of :class:`bottle.Bottle` to
        :func:`glue.start()`.

    :Example:

        >>> app = bottle.Bottle()
        >>> glue.register_glue_routes(app)
        >>> middleware = beaker.middleware.SessionMiddleware(app)
        >>> glue.start(app=middleware)

    """
    for route_path, route_params in BOTTLE_ROUTES.items():
        route_func, route_kwargs = route_params
        app.route(path=route_path, callback=route_func, **route_kwargs)


# Private functions


def _safe_json(obj: Any) -> str:
    return jsn.dumps(obj, default=lambda o: None)


def _repeated_send(ws: WebSocketT, msg: str) -> None:
    for _attempt in range(100):
        try:
            ws.send(msg)
            break
        except Exception:
            sleep(0.001)


def _process_message(message: dict[str, Any], ws: WebSocketT) -> None:
    if 'call' in message:
        error_info: dict[str, str] = {}
        return_val: Any = None
        try:
            name = message['name']
            if name not in _exposed_functions:
                raise KeyError('Function %r is not exposed' % (name,))
            return_val = _exposed_functions[name](*message['args'])
            status = 'ok'
        except Exception as e:
            traceback.print_exc()  # server-side only — do not send stacks to the client
            return_val = None
            status = 'error'
            error_info['errorText'] = repr(e)
        _repeated_send(
            ws,
            _safe_json(
                {
                    'return': message['call'],
                    'status': status,
                    'value': return_val,
                    'error': error_info,
                }
            ),
        )
    elif 'return' in message:
        call_id = message['return']
        if call_id in _call_return_callbacks:
            callback, error_callback = _call_return_callbacks.pop(call_id)
            if message['status'] == 'ok':
                callback(message['value'])
            elif message['status'] == 'error' and error_callback is not None:
                err = message.get('error')
                # Wire shape from JS: {'errorText', 'errorTraceback'} or legacy string+stack
                if isinstance(err, dict):
                    error_callback(err.get('errorText'), err.get('errorTraceback'))
                else:
                    error_callback(err, message.get('stack'))
        else:
            # Sync waiters: unblock even on error (value may be None)
            _call_return_values[call_id] = message.get('value')

    else:
        print('Invalid message received: ', message)


def _get_real_path(path: str) -> str:
    if getattr(sys, 'frozen', False):
        return os.path.join(sys._MEIPASS, path)  # type: ignore # sys._MEIPASS is dynamically added by PyInstaller
    else:
        return os.path.abspath(path)


def _validate_js_name(name: str) -> str:
    if not _JS_NAME_RE.fullmatch(name):
        raise ValueError(
            'Invalid JavaScript function name from glue.expose(): %r '
            '(expected a Python/JS identifier)' % (name,)
        )
    return name


def _mock_js_function(f: str) -> None:
    name = _validate_js_name(f)
    setattr(_this_module, name, lambda *args, _n=name: _mock_call(_n, args))


def _import_js_function(f: str) -> None:
    name = _validate_js_name(f)
    setattr(_this_module, name, lambda *args, _n=name: _js_call(_n, args))


def _call_object(name: str, args: Any) -> dict[str, Any]:
    global _call_number
    _call_number += 1
    call_id = _call_number + rnd.random()
    return {'call': call_id, 'name': name, 'args': args}


def _mock_call(
    name: str, args: Any
) -> Callable[[Callable[..., Any] | None, Callable[..., Any] | None], Any]:
    call_object = _call_object(name, args)
    global _mock_queue
    _mock_queue += [call_object]
    return _call_return(call_object)


def _js_call(
    name: str, args: Any
) -> Callable[[Callable[..., Any] | None, Callable[..., Any] | None], Any]:
    """Call a JS function on the most recently connected Glue page.

    Multi-window note: Python→JS calls are sent to the last websocket only
    (not broadcast), so return values are unambiguous. Open pages that need
    the call must be that latest connection, or call from that page's JS.
    """
    call_object = _call_object(name, args)
    if _websockets:
        _, ws = _websockets[-1]
        _repeated_send(ws, _safe_json(call_object))
    return _call_return(call_object)


def _call_return(
    call: dict[str, Any],
) -> Callable[[Callable[..., Any] | None, Callable[..., Any] | None], Any]:
    global _js_result_timeout
    call_id = call['call']

    def return_func(
        callback: Callable[..., Any] | None = None, error_callback: Callable[..., Any] | None = None
    ) -> Any:
        if callback is not None:
            _call_return_callbacks[call_id] = (callback, error_callback)
        else:
            for _w in range(_js_result_timeout):
                if call_id in _call_return_values:
                    return _call_return_values.pop(call_id)
                sleep(0.001)

    return return_func


def _expose(name: str, function: Callable[..., Any]) -> None:
    name = _validate_js_name(name)
    if name in _exposed_functions:
        raise ValueError('Already exposed function with name "%s"' % name)
    _exposed_functions[name] = function


def _detect_shutdown() -> None:
    if len(_websockets) == 0:
        _close_splash()
        sys.exit()


def _websocket_close(page: str) -> None:
    global _shutdown

    close_callback = _start_args.get('close_callback')

    if close_callback is not None:
        if not callable(close_callback):
            raise TypeError("'close_callback' start_arg/option must be callable or None")
        sockets = [p for _, p in _websockets]
        close_callback(page, sockets)
    else:
        if isinstance(_shutdown, gvt.Greenlet):
            _shutdown.kill()

        _shutdown = gvt.spawn_later(_start_args['shutdown_delay'], _detect_shutdown)


def _set_response_headers(response: btl.Response) -> None:
    if _start_args['disable_cache']:
        # https://stackoverflow.com/a/24748094/280852
        response.set_header('Cache-Control', 'no-store')
