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
    assert browsers._auto_browser_order() == ['edge', 'chrome']
    monkeypatch.setattr(browsers, 'is_windows', lambda: False)
    assert browsers._auto_browser_order() == ['chrome']


def test_open_mode_none_does_not_launch(monkeypatch):
    launched = []

    def boom(*_a, **_k):
        launched.append(True)
        raise AssertionError('browser should not launch')

    monkeypatch.setattr(browsers, '_open_auto', boom)
    monkeypatch.setattr(browsers, '_run_browser', boom)
    browsers.open(['index.html'], {'mode': None, 'host': 'localhost', 'port': 8000})
    browsers.open(['index.html'], {'mode': False, 'host': 'localhost', 'port': 8000})
    assert launched == []


def test_open_unsupported_mode():
    with pytest.raises(ValueError, match='Unsupported mode'):
        browsers.open(['index.html'], {'mode': 'firefox', 'host': 'localhost', 'port': 8000})
