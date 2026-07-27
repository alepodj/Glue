"""PyWebView window host for Glue.

Glue keeps Bottle + WebSockets; this module only owns the native window that
loads ``http://localhost:...``. ``webview.start()`` must run on the main thread
and blocks until all windows close — the Bottle server stays in a real OS
thread when PyWebView is used (gevent greenlets would starve).
"""

from __future__ import annotations

import ctypes
from typing import Any
from urllib.parse import urlparse

from glue.browsers_launcher import platform_name
from glue.types import OptionsDictT

# Keys accepted by webview.start() (not create_window).
_START_KWARG_KEYS = frozenset(
    {
        'func',
        'args',
        'localization',
        'gui',
        'debug',
        'http_server',
        'http_port',
        'user_agent',
        'private_mode',
        'storage_path',
        'menu',
        'server',
        'ssl',
        'server_args',
        'icon',
    }
)

_windows: list[Any] = []
_gui_loop_active: bool = False
_maximized: dict[int, bool] = {}
# Served into glue.js so the page can draw OS-styled chrome when frameless.
_titlebar_config: dict[str, Any] = {
    'enabled': False,
    'platform': 'windows',
}

# In-page title bar heights (px). Native OS chrome is outside the client area;
# these match the CSS bar so we can grow the window and inset content the same way.
TITLEBAR_HEIGHTS: dict[str, int] = {
    'windows': 36,
    'macos': 38,
    'linux': 40,
}


def available() -> bool:
    """Return True if the ``webview`` package can be imported."""
    try:
        import webview  # noqa: F401
    except ImportError:
        return False
    return True


def get_windows() -> list[Any]:
    """Return PyWebView window instances created by the current Glue session."""
    return list(_windows)


def is_gui_loop_active() -> bool:
    return _gui_loop_active


def titlebar_config() -> dict[str, Any]:
    """Config embedded in ``glue.js`` for the in-page title bar."""
    return dict(_titlebar_config)


def titlebar_height(platform: str | None = None) -> int:
    """Pixel height of Glue's in-page title bar for *platform* (or this OS)."""
    name = platform or platform_name()
    return TITLEBAR_HEIGHTS.get(name, TITLEBAR_HEIGHTS['windows'])


def should_try(options: OptionsDictT) -> bool:
    """Whether *auto* mode should attempt PyWebView before Chrome/Edge.

    PyWebView's GUI loop must run on the main thread and blocks, so non-blocking
    starts (``block=False``) skip it and fall through to browser launchers.
    """
    if not options.get('block', True):
        return False
    return available()


def _page_key(url: str) -> str:
    return urlparse(url).path.lstrip('/')


# Default content size when ``glue.start(..., size=None)``.
# ``start()`` stores this in ``_start_args`` so ``/glue.js`` and PyWebView share it.
DEFAULT_WINDOW_SIZE = (1280, 720)


def _geometry_kwargs(url: str, options: OptionsDictT) -> dict[str, Any]:
    """Map Glue size/position/geometry onto create_window kwargs."""
    width, height = DEFAULT_WINDOW_SIZE
    x: int | None = None
    y: int | None = None

    size = options.get('size')
    position = options.get('position')
    if size is not None:
        width, height = size
    if position is not None:
        x, y = position

    geometry = options.get('geometry') or {}
    page_geo = geometry.get(_page_key(url))
    if page_geo:
        if page_geo.get('size'):
            width, height = page_geo['size']  # type: ignore[misc]
        if page_geo.get('position'):
            x, y = page_geo['position']  # type: ignore[misc]

    kwargs: dict[str, Any] = {'width': width, 'height': height}
    if x is not None and y is not None:
        kwargs['x'] = x
        kwargs['y'] = y
    return kwargs


def _split_webview_options(
    options: OptionsDictT,
) -> tuple[dict[str, Any], dict[str, Any], str]:
    raw = dict(options.get('webview_options') or {})
    start_kwargs: dict[str, Any] = {}
    create_defaults: dict[str, Any] = {}
    for key, value in raw.items():
        if key in _START_KWARG_KEYS:
            start_kwargs[key] = value
        else:
            create_defaults[key] = value

    title = options.get('title')
    if title is None:
        title = create_defaults.pop('title', None)
    if not title:
        title = 'Glue'
    return create_defaults, start_kwargs, str(title)


def _glue_create_defaults(options: OptionsDictT | None = None) -> dict[str, Any]:
    """Opinionated Glue window defaults: no browser chrome, OS-styled in-page UI."""
    defaults: dict[str, Any] = {
        # Native title bar / menus off — pages get OS-styled controls via glue.js
        'frameless': True,
        'easy_drag': False,
        'resizable': True if options is None else bool(options.get('resizable', True)),
    }
    if platform_name() == 'windows':
        defaults['shadow'] = True
    return defaults


def _apply_runtime_settings(webview: Any) -> None:
    """Disable PyWebView's default application menus (File / Edit / …)."""
    try:
        webview.settings['SHOW_DEFAULT_MENUS'] = False
    except Exception:
        pass


# Win32 non-client hit-test codes for edge/corner resize (frameless has no OS border).
_WM_NCLBUTTONDOWN = 0x00A1
_HT_RESIZE = {
    'left': 10,
    'right': 11,
    'top': 12,
    'top-left': 13,
    'top-right': 14,
    'bottom': 15,
    'bottom-left': 16,
    'bottom-right': 17,
}


def _window_hwnd(window: Any) -> int | None:
    native = getattr(window, 'native', None)
    if native is None:
        return None
    handle = getattr(native, 'Handle', None)
    if handle is None:
        return None
    try:
        return int(handle.ToInt32())
    except Exception:
        try:
            return int(handle)
        except Exception:
            return None


def _start_win32_resize(window: Any, edge: str) -> bool:
    """Begin a native Windows resize drag from a frameless edge/corner."""
    ht = _HT_RESIZE.get(edge)
    hwnd = _window_hwnd(window)
    if ht is None or hwnd is None:
        return False

    user32 = ctypes.windll.user32

    def _do() -> None:
        user32.ReleaseCapture()
        user32.SendMessageW(hwnd, _WM_NCLBUTTONDOWN, ht, 0)

    native = getattr(window, 'native', None)
    try:
        # Marshal onto the WinForms UI thread when possible.
        from System import Action  # type: ignore

        if native is not None and hasattr(native, 'BeginInvoke'):
            native.BeginInvoke(Action(_do))
            return True
    except Exception:
        pass

    _do()
    return True


def _register_window_api() -> None:
    """Expose minimize / maximize / close / resize to JavaScript via the Glue bridge."""
    import glue as glue_mod

    if 'webview_minimize' in glue_mod._exposed_functions:
        return

    def webview_minimize() -> None:
        for window in get_windows():
            window.minimize()

    def webview_toggle_maximize() -> None:
        for window in get_windows():
            key = id(window)
            if _maximized.get(key, bool(getattr(window, 'maximized', False))):
                window.restore()
                _maximized[key] = False
                try:
                    window.maximized = False
                except Exception:
                    pass
            else:
                window.maximize()
                _maximized[key] = True
                try:
                    window.maximized = True
                except Exception:
                    pass

    def webview_close() -> None:
        for window in list(get_windows()):
            window.destroy()

    def webview_platform() -> str:
        return platform_name()

    def webview_start_resize(edge: str) -> bool:
        """Start an OS resize drag. Needed on Windows where frameless has no border."""
        if platform_name() != 'windows':
            return False
        if not isinstance(edge, str):
            return False
        ok = False
        for window in get_windows():
            if _maximized.get(id(window), bool(getattr(window, 'maximized', False))):
                continue
            if _start_win32_resize(window, edge):
                ok = True
        return ok

    glue_mod._expose('webview_minimize', webview_minimize)
    glue_mod._expose('webview_toggle_maximize', webview_toggle_maximize)
    glue_mod._expose('webview_close', webview_close)
    glue_mod._expose('webview_platform', webview_platform)
    glue_mod._expose('webview_start_resize', webview_start_resize)


def _default_favicon_path() -> str | None:
    """Prefer ``favicon.ico`` from the Glue UI folder when present."""
    try:
        import glue as glue_mod

        root = getattr(glue_mod, 'root_path', None)
    except Exception:
        return None
    if not root:
        return None
    import os

    path = os.path.join(root, 'favicon.ico')
    return path if os.path.isfile(path) else None


def _window_icon_path(options: OptionsDictT) -> str | None:
    """Resolve native window icon: explicit ``icon`` / webview_options, else ``ui/favicon.ico``."""
    raw = options.get('webview_options') or {}
    explicit = raw.get('icon')
    if isinstance(explicit, str) and explicit.strip():
        return explicit
    return _default_favicon_path()


def _create_windows(
    webview: Any,
    options: OptionsDictT,
    start_urls: list[str],
) -> None:
    global _windows, _titlebar_config
    user_defaults, _, title = _split_webview_options(options)
    create_defaults = _glue_create_defaults(options)
    create_defaults.update(user_defaults)

    frameless = bool(create_defaults.get('frameless', True))
    resizable = bool(create_defaults.get('resizable', True))
    icon_path = _window_icon_path(options)
    # Native window icon (taskbar / Alt+Tab) on create_window. ``webview.start(icon=…)``
    # is also set in open_urls for backends that read it there.
    # Note: under ``python.exe`` Windows may still show the Python taskbar icon;
    # freeze with PyInstaller (exe icon) for a reliable app identity.
    if icon_path:
        create_defaults['icon'] = icon_path
    favicon_path = _default_favicon_path()
    bar_h = titlebar_height()
    _titlebar_config = {
        'enabled': frameless,
        'platform': platform_name(),
        'title': title,
        # In-page titlebar icon (URL). Override via webview chrome config later if needed.
        'icon': '/favicon.ico' if favicon_path else None,
        # Native title bars sit outside the client area; we grow the window by
        # this amount and inset page content so size=(w,h) stays content pixels.
        'titlebar_height': bar_h if frameless else 0,
        'resizable': resizable,
        # Frameless Windows has no OS resize border — glue.js installs edge grips.
        'resize_grips': bool(frameless and resizable and platform_name() == 'windows'),
    }


    for url in start_urls:
        kwargs = dict(create_defaults)
        kwargs.update(_geometry_kwargs(url, options))
        if frameless:
            kwargs['height'] = int(kwargs['height']) + bar_h
        kwargs['title'] = title
        kwargs['url'] = url
        window = webview.create_window(**kwargs)
        _windows.append(window)
        _maximized[id(window)] = bool(kwargs.get('maximized', False))
        if frameless and resizable and platform_name() == 'windows':
            # Must be pywebview.api (sync-ish), not Glue websockets — Win32
            # WM_NCLBUTTONDOWN has to run while the mouse button is still down.
            def webview_start_resize(edge: str, _win: Any = window) -> bool:
                if _maximized.get(id(_win), bool(getattr(_win, 'maximized', False))):
                    return False
                return _start_win32_resize(_win, edge)

            try:
                window.expose(webview_start_resize)
            except Exception:
                pass


def open_urls(
    options: OptionsDictT,
    start_urls: list[str],
    *,
    required: bool = False,
) -> str:
    """Open *start_urls* in PyWebView.

    Returns:
        ``'completed'`` — primary GUI loop ran and finished (all windows closed).
        ``'shown'`` — windows created while the GUI loop was already running.
        ``'unavailable'`` — could not use PyWebView (caller may fall back).

    When *required* is True, failures raise ``EnvironmentError`` / ``ValueError``
    instead of returning ``'unavailable'``.
    """
    global _gui_loop_active, _windows, _titlebar_config

    if not options.get('block', True) and not _gui_loop_active:
        msg = (
            "mode 'webview' requires block=True because pywebview.start() "
            'must run on the main thread'
        )
        if required:
            raise ValueError(msg)
        return 'unavailable'

    try:
        import webview
    except ImportError:
        if required:
            raise OSError(
                'PyWebView is not installed. Install with: pip install pywebview'
            ) from None
        return 'unavailable'

    _, start_kwargs, _title = _split_webview_options(options)
    # No default File/Edit menus unless the app passes menu= explicitly.
    start_kwargs.setdefault('menu', [])
    icon_path = _window_icon_path(options)
    if icon_path and 'icon' not in start_kwargs:
        start_kwargs['icon'] = icon_path

    try:
        _apply_runtime_settings(webview)
        _register_window_api()

        if _gui_loop_active:
            _create_windows(webview, options, start_urls)
            return 'shown'

        _windows = []
        _maximized.clear()
        _create_windows(webview, options, start_urls)
        _gui_loop_active = True
        try:
            webview.start(**start_kwargs)
        finally:
            _gui_loop_active = False
            _titlebar_config = {'enabled': False, 'platform': platform_name()}
        return 'completed'
    except Exception as exc:
        _gui_loop_active = False
        _windows = []
        _titlebar_config = {'enabled': False, 'platform': platform_name()}
        if required:
            raise OSError('Failed to start PyWebView: %s' % exc) from exc
        # Avoid leaving half-configured state before Chrome/Edge fallback.
        try:
            webview.windows.clear()
        except Exception:
            pass
        return 'unavailable'
