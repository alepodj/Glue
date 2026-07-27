"""glue.init — UI root discovery and JS expose scanning."""

import glue
from tests.helpers import TEST_DATA_DIR

INIT_DIR = TEST_DATA_DIR / 'init_test'


def test_init_scans_js_exposes():
    glue.init(path=INIT_DIR)
    expected = ['js_random', 'say_hello_js', 'show_log', 'show_log_alt']
    assert sorted(glue._js_functions) == expected
    assert callable(glue.say_hello_js)
    assert callable(glue.js_random)


def test_init_default_path_is_ui(tmp_path, monkeypatch):
    ui = tmp_path / 'ui'
    ui.mkdir()
    (ui / 'index.html').write_text('<html></html>', encoding='utf-8')
    monkeypatch.chdir(tmp_path)
    glue.init()
    assert glue.root_path == str(ui.resolve())
