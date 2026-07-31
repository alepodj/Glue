"""Repository examples stay runnable, standalone, and consistently presented."""

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
EXAMPLES = ROOT / 'examples'
EXAMPLE_DIRS = tuple(
    sorted(path for path in EXAMPLES.iterdir() if path.is_dir() and path.name[:2].isdigit())
)

ENTRY_PAGES = (
    EXAMPLES / '00 - presentation' / 'ui' / 'index.html',
    EXAMPLES / '01 - hello_world' / 'ui' / 'index.html',
    EXAMPLES / '02 - hello_world_chrome' / 'ui' / 'index.html',
    EXAMPLES / '03 - callbacks' / 'ui' / 'index.html',
    EXAMPLES / '04 - sync_callbacks' / 'ui' / 'index.html',
    EXAMPLES / '05 - file_access' / 'ui' / 'index.html',
    EXAMPLES / '06 - input' / 'ui' / 'index.html',
    EXAMPLES / '07 - jinja_templates' / 'ui' / 'templates' / 'base.html',
    EXAMPLES / '09 - disable_cache' / 'ui' / 'index.html',
    EXAMPLES / '10 - custom_app_routes' / 'ui' / 'index.html',
    EXAMPLES / '11 - splash' / 'ui' / 'index.html',
    EXAMPLES / '12 - scrolling' / 'ui' / 'index.html',
)


def test_numbered_examples_are_contiguous():
    numbered = [int(path.name.split(' ', 1)[0]) for path in EXAMPLE_DIRS]
    assert numbered == list(range(13))


@pytest.mark.parametrize('example', EXAMPLE_DIRS, ids=lambda path: path.name)
def test_examples_use_standard_entrypoint_names_and_readmes(example):
    name = example.name.split(' - ', 1)[1]
    assert (example / f'{name}.py').is_file()
    readme = (example / 'README.md').read_text(encoding='utf-8')
    for section in ('## What it demonstrates', '## Files', '## Run', '## Key API'):
        assert section in readme


def test_primary_html_uses_index_filename():
    conventional = tuple(
        example
        for example in EXAMPLE_DIRS
        if example.name not in {'07 - jinja_templates', '08 - createreactapp'}
    )
    assert all((example / 'ui' / 'index.html').is_file() for example in conventional)
    assert (EXAMPLES / '07 - jinja_templates' / 'ui' / 'templates' / 'index.html').is_file()
    assert (EXAMPLES / '08 - createreactapp' / 'public' / 'index.html').is_file()


@pytest.mark.parametrize('script', sorted(EXAMPLES.glob('**/*.py')), ids=lambda path: path.name)
def test_example_python_compiles(script):
    compile(script.read_text(encoding='utf-8'), str(script), 'exec')


def test_examples_do_not_patch_python_import_paths():
    for script in EXAMPLES.glob('**/*.py'):
        source = script.read_text(encoding='utf-8')
        assert 'sys.path.insert' not in source, script


def test_standalone_javascript_uses_app_filename():
    scripts = [
        script for script in EXAMPLES.glob('**/*.js') if '08 - createreactapp' not in script.parts
    ]
    assert scripts
    assert all(script.name == 'app.js' for script in scripts)


@pytest.mark.parametrize('page', ENTRY_PAGES, ids=lambda path: path.parent.parent.name)
def test_entry_pages_have_bridge_metadata_and_presentation(page):
    source = page.read_text(encoding='utf-8')
    assert '<html lang=' in source
    assert 'name="viewport"' in source
    assert '/glue.js' in source
    assert '<style>' in source or 'styles.css' in source


def test_input_example_has_no_network_ui_dependencies():
    source = (EXAMPLES / '06 - input' / 'ui' / 'index.html').read_text(encoding='utf-8')
    assert 'http://' not in source
    assert 'https://' not in source
