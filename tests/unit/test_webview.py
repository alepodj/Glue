"""PyWebView host: geometry, defaults, title bar, option merge."""

import glue
import glue.browsers_launcher as browsers_launcher
import glue.webview as webview


def test_geometry_kwargs_page_override():
    kwargs = webview._geometry_kwargs(
        'http://localhost:8000/hello.html',
        {
            'size': (1280, 720),
            'position': (10, 20),
            'geometry': {
                'hello.html': {'size': (640, 480), 'position': (1, 2)},
            },
        },
    )
    assert kwargs == {'width': 640, 'height': 480, 'x': 1, 'y': 2}


def test_default_size_when_size_none():
    w, h = webview.DEFAULT_WINDOW_SIZE
    kwargs = webview._geometry_kwargs(
        'http://localhost:8000/index.html',
        {'size': None, 'position': None, 'geometry': {}},
    )
    assert kwargs == {'width': w, 'height': h}


def test_glue_js_start_geometry_uses_size():
    w, h = webview.DEFAULT_WINDOW_SIZE
    prev = dict(glue._start_args)
    try:
        glue._start_args.update(
            {
                'size': (w, h),
                'position': None,
                'geometry': {},
                'disable_cache': False,
            }
        )
        js = glue._glue()
        assert '"size": [%d, %d]' % (w, h) in js
    finally:
        glue._start_args.clear()
        glue._start_args.update(prev)


def test_merge_webview_options_first_class_wins():
    merged = glue._merge_webview_options(
        {'frameless': True, 'debug': False, 'private_mode': True},
        frameless=False,
        debug=True,
        gui=None,
    )
    assert merged['frameless'] is False
    assert merged['debug'] is True
    assert merged['private_mode'] is True
    assert 'gui' not in merged


def test_create_defaults_are_frameless():
    defaults = webview._glue_create_defaults()
    assert defaults['frameless'] is True
    assert defaults['easy_drag'] is False
    assert defaults['resizable'] is True
    assert webview._glue_create_defaults({'resizable': False})['resizable'] is False


def test_titlebar_heights():
    assert webview.titlebar_height('windows') == 36
    assert webview.titlebar_height('macos') == 38
    assert webview.titlebar_height('linux') == 40


def test_platform_name(monkeypatch):
    monkeypatch.setattr(browsers_launcher.sys, 'platform', 'win32')
    assert webview.platform_name() == 'windows'
    monkeypatch.setattr(browsers_launcher.sys, 'platform', 'darwin')
    assert webview.platform_name() == 'macos'
    monkeypatch.setattr(browsers_launcher.sys, 'platform', 'linux')
    assert webview.platform_name() == 'linux'
