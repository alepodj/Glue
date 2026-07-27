"""@glue.expose and static JS expose() discovery."""

import pytest

import glue
from tests.helpers import TEST_DATA_DIR

INIT_DIR = TEST_DATA_DIR / 'init_test'


@pytest.fixture(autouse=True)
def _clean_exposed():
    before = dict(glue._exposed_functions)
    yield
    glue._exposed_functions.clear()
    glue._exposed_functions.update(before)


@pytest.mark.parametrize(
    'js_code, expected_matches',
    [
        ('glue.expose(w,"say_hello_js")', ['say_hello_js']),
        ('glue.expose(function(e){console.log(e)},"show_log_alt")', ['show_log_alt']),
        (
            ' \t\nwindow.glue.expose((function show_log(e) {console.log(e)}), "show_log")\n',
            ['show_log'],
        ),
        ((INIT_DIR / 'minified.js').read_text(), ['say_hello_js', 'show_log_alt', 'show_log']),
        ((INIT_DIR / 'sample.html').read_text(), ['say_hello_js']),
        ((INIT_DIR / 'App.tsx').read_text(), ['say_hello_js', 'show_log']),
        ((INIT_DIR / 'hello.html').read_text(), ['say_hello_js', 'js_random']),
    ],
)
def test_parse_exposed_js_functions(js_code, expected_matches):
    matches = glue.EXPOSED_JS_FUNCTIONS.parse_string(js_code).as_list()
    assert matches == expected_matches


def test_validate_js_name():
    assert glue._validate_js_name('say_hello_js') == 'say_hello_js'
    with pytest.raises(ValueError):
        glue._validate_js_name('bad-name')
    with pytest.raises(ValueError):
        glue._validate_js_name('foo(bar)')


def test_expose_rejects_invalid_name():
    with pytest.raises(ValueError, match='Invalid JavaScript function name'):

        @glue.expose('bad-name')
        def _fn():
            return None


def test_expose_rejects_duplicate():
    def a():
        return 1

    def b():
        return 2

    glue._expose('dup_fn', a)
    with pytest.raises(ValueError, match='Already exposed'):
        glue._expose('dup_fn', b)


def test_expose_accepts_valid_identifier():
    @glue.expose('ok_fn')
    def ok_fn():
        return 42

    assert 'ok_fn' in glue._exposed_functions
