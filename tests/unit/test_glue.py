import glue
import glue.browsers as browsers
import pytest
from tests.utils import TEST_DATA_DIR

# Directory for testing glue.__init__
INIT_DIR = TEST_DATA_DIR / 'init_test'


@pytest.mark.parametrize('js_code, expected_matches', [
    ('glue.expose(w,"say_hello_js")', ['say_hello_js']),
    ('glue.expose(function(e){console.log(e)},"show_log_alt")', ['show_log_alt']),
    (' \t\nwindow.glue.expose((function show_log(e) {console.log(e)}), "show_log")\n', ['show_log']),
    ((INIT_DIR / 'minified.js').read_text(), ['say_hello_js', 'show_log_alt', 'show_log']),
    ((INIT_DIR / 'sample.html').read_text(), ['say_hello_js']),
    ((INIT_DIR / 'App.tsx').read_text(), ['say_hello_js', 'show_log']),
    ((INIT_DIR / 'hello.html').read_text(), ['say_hello_js', 'js_random']),
])
def test_exposed_js_functions(js_code, expected_matches):
    """Test the PyParsing PEG against several specific test cases."""
    matches = glue.EXPOSED_JS_FUNCTIONS.parseString(js_code).asList()
    assert matches == expected_matches, f'Expected {expected_matches} (found: {matches}) in: {js_code}'


def test_validate_js_name():
    assert glue._validate_js_name('say_hello_js') == 'say_hello_js'
    with pytest.raises(ValueError):
        glue._validate_js_name('bad-name')
    with pytest.raises(ValueError):
        glue._validate_js_name('foo(bar)')


def test_init():
    """Test glue.init() against a test directory and ensure that all JS functions are in the global _js_functions."""
    glue.init(path=INIT_DIR)
    expected = ['js_random', 'say_hello_js', 'show_log', 'show_log_alt']
    assert sorted(glue._js_functions) == expected, (
        f'Expected {expected} (found: {sorted(glue._js_functions)}) in {INIT_DIR}'
    )
    # Stubs are installed on the glue module without exec
    assert callable(glue.say_hello_js)
    assert callable(glue.js_random)


def test_init_default_path_is_ui(tmp_path, monkeypatch):
    """glue.init() with no path argument serves the default ui/ folder."""
    ui = tmp_path / 'ui'
    ui.mkdir()
    (ui / 'index.html').write_text('<html></html>', encoding='utf-8')
    monkeypatch.chdir(tmp_path)
    glue.init()
    assert glue.root_path == str(ui.resolve())


def test_build_urls_from_string_and_dict():
    options = {'host': '127.0.0.1', 'port': 9000}
    urls = browsers._build_urls(
        ['hello.html', {'path': 'other.html', 'host': 'localhost', 'port': '9001'}],
        options,
    )
    assert urls == [
        'http://127.0.0.1:9000/hello.html',
        'http://localhost:9001/other.html',
    ]


def test_auto_browser_order(monkeypatch):
    monkeypatch.setattr(browsers, 'is_windows', lambda: True)
    assert browsers._auto_browser_order() == ['chrome', 'edge']
    monkeypatch.setattr(browsers, 'is_windows', lambda: False)
    assert browsers._auto_browser_order() == ['chrome']


def test_auto_tries_webview_before_browsers(monkeypatch):
    calls = []

    monkeypatch.setattr(browsers.webview, 'should_try', lambda _opts: True)

    def fake_webview(options, start_urls, *, required):
        calls.append(('webview', required))
        browsers._webview_session_completed = True
        return 'completed'

    def boom(*_a, **_k):
        raise AssertionError('browser should not launch when webview succeeds')

    monkeypatch.setattr(browsers, '_open_webview', fake_webview)
    monkeypatch.setattr(browsers, '_run_browser', boom)
    browsers.open(
        ['index.html'],
        {'mode': 'auto', 'host': 'localhost', 'port': 8000, 'block': True},
    )
    assert calls == [('webview', False)]
    assert browsers.webview_session_completed() is True


def test_auto_falls_back_when_webview_unavailable(monkeypatch):
    calls = []

    monkeypatch.setattr(browsers.webview, 'should_try', lambda _opts: True)
    monkeypatch.setattr(
        browsers,
        '_open_webview',
        lambda *_a, **_k: 'unavailable',
    )
    monkeypatch.setattr(browsers, 'is_windows', lambda: True)

    def fake_run(name, options, start_urls):
        calls.append(name)
        return name == 'chrome'

    monkeypatch.setattr(browsers, '_run_browser', fake_run)
    browsers.open(
        ['index.html'],
        {'mode': 'auto', 'host': 'localhost', 'port': 8000, 'block': True},
    )
    assert calls == ['chrome']


def test_auto_skips_webview_when_not_blocking(monkeypatch):
    calls = []

    def boom_webview(*_a, **_k):
        raise AssertionError('webview should be skipped when block=False')

    monkeypatch.setattr(browsers.webview, 'should_try', lambda opts: False)
    monkeypatch.setattr(browsers, '_open_webview', boom_webview)
    monkeypatch.setattr(browsers, 'is_windows', lambda: False)

    def fake_run(name, options, start_urls):
        calls.append(name)
        return True

    monkeypatch.setattr(browsers, '_run_browser', fake_run)
    browsers.open(
        ['index.html'],
        {'mode': 'auto', 'host': 'localhost', 'port': 8000, 'block': False},
    )
    assert calls == ['chrome']


def test_webview_mode_requires_block(monkeypatch):
    monkeypatch.setattr(browsers.webview, 'available', lambda: True)
    with pytest.raises(ValueError, match='block=True'):
        browsers.open(
            ['index.html'],
            {'mode': 'webview', 'host': 'localhost', 'port': 8000, 'block': False},
        )


def test_open_mode_none_does_not_launch(monkeypatch):
    launched = []

    def boom(*_a, **_k):
        launched.append(True)
        raise AssertionError('browser should not launch')

    monkeypatch.setattr(browsers, '_open_auto', boom)
    monkeypatch.setattr(browsers, '_run_browser', boom)
    monkeypatch.setattr(browsers, '_open_webview', boom)
    browsers.open(['index.html'], {'mode': None, 'host': 'localhost', 'port': 8000})
    browsers.open(['index.html'], {'mode': False, 'host': 'localhost', 'port': 8000})
    assert launched == []


def test_open_unsupported_mode():
    with pytest.raises(ValueError, match='Unsupported mode'):
        browsers.open(['index.html'], {'mode': 'firefox', 'host': 'localhost', 'port': 8000})


def test_webview_geometry_kwargs():
    import glue.webview as webview

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


def test_webview_create_defaults_are_frameless():
    import glue.webview as webview

    defaults = webview._glue_create_defaults()
    assert defaults['frameless'] is True
    assert defaults['easy_drag'] is False
    assert defaults['resizable'] is True
    assert webview._glue_create_defaults({'resizable': False})['resizable'] is False


def test_webview_titlebar_heights():
    import glue.webview as webview

    assert webview.titlebar_height('windows') == 36
    assert webview.titlebar_height('macos') == 38
    assert webview.titlebar_height('linux') == 40


def test_webview_platform_name(monkeypatch):
    import glue.browsers_launcher as browsers_launcher
    import glue.webview as webview

    monkeypatch.setattr(browsers_launcher.sys, 'platform', 'win32')
    assert webview.platform_name() == 'windows'
    monkeypatch.setattr(browsers_launcher.sys, 'platform', 'darwin')
    assert webview.platform_name() == 'macos'
    monkeypatch.setattr(browsers_launcher.sys, 'platform', 'linux')
    assert webview.platform_name() == 'linux'


def test_browsers_launcher_helpers_exist():
    import glue.browsers_launcher as browsers_launcher

    assert callable(browsers_launcher.find_app_path_win)
    assert callable(browsers_launcher.find_mac_app)
    assert browsers_launcher.platform_name() in ('windows', 'macos', 'linux')