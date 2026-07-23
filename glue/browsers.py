from __future__ import annotations
import subprocess as sps
import sys
from typing import Union, List, Dict, Iterable, Optional
from types import ModuleType

from glue.types import OptionsDictT
import glue.chrome as chm
import glue.edge as edge

_browser_paths: Dict[str, str] = {}
_browser_modules: Dict[str, ModuleType] = {
    'chrome': chm,
    'edge': edge,
}


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
    # Prefer Edge on Windows (preinstalled); Chrome/Chromium everywhere else,
    # and as fallback on Windows when Edge is unavailable.
    if sys.platform in ['win32', 'win64'] or sys.platform.startswith('win'):
        return ['edge', 'chrome']
    return ['chrome']


def _open_auto(options: OptionsDictT, start_urls: List[str]) -> None:
    tried = _auto_browser_order()
    for browser_name in tried:
        if _run_browser(browser_name, options, start_urls):
            return
    names = ' or '.join(m.name for m in (_browser_modules[n] for n in tried))
    raise EnvironmentError(
        "Can't find a supported browser (%s). "
        "Install Microsoft Edge or Google Chrome/Chromium." % names
    )


def open(start_pages: Iterable[Union[str, Dict[str, str]]], options: OptionsDictT) -> None:
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
            "Unsupported mode %r. Use 'auto', 'chrome', 'edge', 'custom', None, or False."
            % (mode,)
        )


def set_path(browser_name: str, path: str) -> None:
    _browser_paths[browser_name] = path


def get_path(browser_name: str) -> Optional[str]:
    return _browser_paths.get(browser_name)
