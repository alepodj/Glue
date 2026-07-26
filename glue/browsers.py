from __future__ import annotations
import subprocess as sps
from typing import Union, List, Dict, Iterable, Optional
from types import ModuleType

from glue.types import OptionsDictT
import glue.chrome as chm
import glue.edge as edge
import glue.webview_host as webview_host
from glue.chromium import is_windows

_browser_paths: Dict[str, str] = {}
_browser_modules: Dict[str, ModuleType] = {
    'chrome': chm,
    'edge': edge,
}

WEBVIEW_MODES = frozenset({'webview', 'pywebview'})

# Set when PyWebView's primary GUI loop has returned (all windows closed).
# ``glue.start`` uses this to exit cleanly instead of joining the server forever.
_webview_session_completed: bool = False


def webview_session_completed() -> bool:
    return _webview_session_completed


def _build_url_from_dict(page: Dict[str, str], options: OptionsDictT) -> str:
    scheme = page.get('scheme', 'http')
    host = page.get('host', 'localhost')
    port = page.get('port', options["port"])
    path = page.get('path', '')
    if not isinstance(port, (int, str)):
        raise TypeError("'port' option must be an integer")
    return '%s://%s:%d/%s' % (scheme, host, int(port), path)


def _build_url_from_string(page: str, options: OptionsDictT) -> str:
    if not isinstance(options['port'], (int, str)):
        raise TypeError("'port' option must be an integer")
    base_url = 'http://%s:%d/' % (options['host'], int(options['port']))
    return base_url + page


def _build_urls(start_pages: Iterable[Union[str, Dict[str, str]]], options: OptionsDictT) -> List[str]:
    urls: List[str] = []

    for page in start_pages:
        if isinstance(page, dict):
            url = _build_url_from_dict(page, options)
        else:
            url = _build_url_from_string(page, options)
        urls.append(url)

    return urls


def _resolved_path(browser_name: str) -> Optional[str]:
    path = _browser_paths.get(browser_name)
    if path is None:
        path = _browser_modules[browser_name].find_path()
        if path is not None:
            _browser_paths[browser_name] = path
    return path


def _run_browser(browser_name: str, options: OptionsDictT, start_urls: List[str]) -> bool:
    browser_module = _browser_modules[browser_name]
    path = _resolved_path(browser_name)
    if path is None:
        return False
    browser_module.run(path, options, start_urls)
    return True


def _auto_browser_order() -> List[str]:
    # Prefer Chrome/Chromium everywhere for consistent app-mode behavior.
    # On Windows only, fall back to Edge if Chrome/Chromium is missing.
    if is_windows():
        return ['chrome', 'edge']
    return ['chrome']


def _open_webview(options: OptionsDictT, start_urls: List[str], *, required: bool) -> str:
    """Launch via PyWebView. Returns webview_host.open_urls status string."""
    global _webview_session_completed
    result = webview_host.open_urls(options, start_urls, required=required)
    if result == 'completed':
        _webview_session_completed = True
    return result


def _open_auto(options: OptionsDictT, start_urls: List[str]) -> None:
    # PyWebView (all OS) → Chrome (all OS) → Edge (Windows only)
    if webview_host.should_try(options):
        result = _open_webview(options, start_urls, required=False)
        if result in ('completed', 'shown'):
            return

    tried = _auto_browser_order()
    for browser_name in tried:
        if _run_browser(browser_name, options, start_urls):
            return
    if is_windows():
        raise EnvironmentError(
            "Can't find PyWebView, Google Chrome/Chromium, or Microsoft Edge. "
            "Install pywebview (preferred), Chrome/Chromium, or Edge."
        )
    raise EnvironmentError(
        "Can't find PyWebView or Google Chrome/Chromium. "
        "Install pywebview (preferred) or Chrome/Chromium to run Glue apps "
        "on this platform."
    )


def open(start_pages: Iterable[Union[str, Dict[str, str]]], options: OptionsDictT) -> None:
    global _webview_session_completed
    if not webview_host.is_gui_loop_active():
        _webview_session_completed = False
    # Build full URLs for starting pages (including host and port)
    start_urls = _build_urls(start_pages, options)

    mode = options.get('mode')
    if not isinstance(mode, (str, type(None))) and mode is not False:
        raise TypeError("'mode' option must by either a string, False, or None")
    if mode is None or mode is False:
        # Don't open a browser (server-only / tests)
        pass
    elif mode == 'auto':
        _open_auto(options, start_urls)
    elif mode in WEBVIEW_MODES:
        _open_webview(options, start_urls, required=True)
    elif mode == 'custom':
        # Advanced escape hatch: run whatever command the user provided
        if not isinstance(options['cmdline_args'], list):
            raise TypeError("'cmdline_args' option must be of type List[str]")
        sps.Popen(options['cmdline_args'],
                  stdout=sps.PIPE, stderr=sps.PIPE, stdin=sps.PIPE)
    elif mode in _browser_modules:
        if not _run_browser(mode, options, start_urls):
            raise EnvironmentError("Can't find %s installation" % _browser_modules[mode].name)
    else:
        raise ValueError(
            "Unsupported mode %r. Use 'auto', 'webview'/'pywebview', 'chrome', "
            "'edge', 'custom', None, or False." % (mode,)
        )


def set_path(browser_name: str, path: str) -> None:
    _browser_paths[browser_name] = path


def get_path(browser_name: str) -> Optional[str]:
    return _browser_paths.get(browser_name)
