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


def test_glue_js_includes_window_title_when_set():
    prev = dict(glue._start_args)
    try:
        glue._start_args.update(
            {
                'size': (800, 600),
                'position': None,
                'geometry': {},
                'disable_cache': False,
                'title': 'Faro',
            }
        )
        js = glue._glue()
        assert '_window_title: "Faro"' in js
    finally:
        glue._start_args.clear()
        glue._start_args.update(prev)


def test_glue_js_window_title_null_when_unset():
    prev = dict(glue._start_args)
    try:
        glue._start_args.update(
            {
                'size': (800, 600),
                'position': None,
                'geometry': {},
                'disable_cache': False,
                'title': None,
            }
        )
        js = glue._glue()
        assert '_window_title: null' in js
    finally:
        glue._start_args.clear()
        glue._start_args.update(prev)


def test_glue_js_favicon_href_when_present(tmp_path):
    favicon = tmp_path / 'favicon.ico'
    favicon.write_bytes(b'\x00\x00\x01\x00')
    prev = dict(glue._start_args)
    prev_root = getattr(glue, 'root_path', None)
    try:
        glue.root_path = str(tmp_path)
        glue._start_args.update(
            {
                'size': (800, 600),
                'position': None,
                'geometry': {},
                'disable_cache': False,
                'title': None,
            }
        )
        js = glue._glue()
        assert '_favicon_href: "/favicon.ico?v=' in js
    finally:
        if prev_root is None:
            try:
                delattr(glue, 'root_path')
            except AttributeError:
                glue.root_path = None  # type: ignore[attr-defined]
        else:
            glue.root_path = prev_root
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


def test_titlebar_owns_viewport_and_content_owns_scrolling():
    js = glue._glue_js
    assert 'html.glue-webview-chrome {' in js
    assert 'overflow: hidden;' in js
    assert 'overflow-y: var(--glue-content-overflow-y, auto);' in js
    assert 'contentOverflow(bodyOverflow.overflowY, rootOverflow.overflowY)' in js
    assert 'contain: layout style paint; isolation: isolate;' in js


def test_platform_name(monkeypatch):
    monkeypatch.setattr(browsers_launcher.sys, 'platform', 'win32')
    assert webview.platform_name() == 'windows'
    monkeypatch.setattr(browsers_launcher.sys, 'platform', 'darwin')
    assert webview.platform_name() == 'macos'
    monkeypatch.setattr(browsers_launcher.sys, 'platform', 'linux')
    assert webview.platform_name() == 'linux'


def test_create_window_does_not_receive_icon(monkeypatch, tmp_path):
    """PyWebView 6.x rejects create_window(..., icon=); icon is start()-only."""
    favicon = tmp_path / 'favicon.ico'
    favicon.write_bytes(b'\x00\x00\x01\x00')
    glue.root_path = str(tmp_path)

    created = []

    class FakeWebview:
        @staticmethod
        def create_window(**kwargs):
            created.append(kwargs)

            class W:
                pass

            return W()

    monkeypatch.setattr(webview, 'platform_name', lambda: 'windows')
    webview._windows.clear()
    try:
        webview._create_windows(
            FakeWebview(),
            {
                'size': (800, 600),
                'position': None,
                'geometry': {},
                'webview_options': {'icon': str(favicon)},
                'resizable': True,
            },
            ['http://localhost:8000/index.html'],
        )
    finally:
        webview._windows.clear()

    assert len(created) == 1
    assert 'icon' not in created[0]


def test_open_urls_passes_icon_to_start_only(monkeypatch, tmp_path):
    favicon = tmp_path / 'favicon.ico'
    favicon.write_bytes(b'\x00\x00\x01\x00')
    glue.root_path = str(tmp_path)

    start_calls = []
    create_calls = []

    class FakeWindow:
        def expose(self, *_a, **_k):
            return None

    class FakeWebviewMod:
        settings = {}

        @staticmethod
        def create_window(**kwargs):
            create_calls.append(kwargs)
            return FakeWindow()

        @staticmethod
        def start(**kwargs):
            start_calls.append(kwargs)

    import sys

    monkeypatch.setitem(sys.modules, 'webview', FakeWebviewMod)
    monkeypatch.setattr(webview, '_register_window_api', lambda: None)
    monkeypatch.setattr(webview, 'platform_name', lambda: 'windows')
    webview._gui_loop_active = False
    webview._windows.clear()
    try:
        result = webview.open_urls(
            {
                'block': True,
                'size': (800, 600),
                'position': None,
                'geometry': {},
                'webview_options': {},
                'resizable': True,
                'title': 'Test',
            },
            ['http://localhost:8000/index.html'],
            required=False,
        )
    finally:
        webview._gui_loop_active = False
        webview._windows.clear()

    assert result == 'completed'
    assert create_calls and 'icon' not in create_calls[0]
    assert start_calls and start_calls[0].get('icon') == str(favicon)
