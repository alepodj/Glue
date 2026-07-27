import importlib
import json
from pathlib import Path

import pytest

import glue

settings_mod = importlib.import_module('glue.settings')


@pytest.fixture(autouse=True)
def _reset_settings(monkeypatch, tmp_path):
    settings_mod.reset()
    monkeypatch.setenv('HOME', str(tmp_path))
    monkeypatch.setenv('USERPROFILE', str(tmp_path))
    # Path.home() on Windows may ignore HOME; force via expanduser if needed
    monkeypatch.setattr(Path, 'home', classmethod(lambda cls: tmp_path))
    yield
    settings_mod.reset()


def test_settings_requires_app_name_for_default():
    with pytest.raises(RuntimeError, match='app_name'):
        glue.settings()
    with pytest.raises(RuntimeError, match='app_name'):
        glue.settings_path()
    with pytest.raises(RuntimeError, match='app_name'):
        glue.save_settings({'a': 1})


def test_settings_custom_path_without_app_name(tmp_path):
    path = tmp_path / 'custom.json'
    assert glue.settings(str(path)) == {}
    assert not path.exists()

    data = {'theme': 'dark', 'nested': {'n': 1}}
    written = glue.save_settings(data, str(path))
    assert Path(written) == path.resolve()
    assert path.is_file()
    assert json.loads(path.read_text(encoding='utf-8')) == data
    assert glue.settings(str(path)) == data


def test_default_path_round_trip(tmp_path):
    glue.init(path=tmp_path, app_name='myapp')
    # Create a dummy ui-less init: path must exist for walk
    expected = tmp_path / '.myapp' / 'myapp.json'
    assert Path(glue.settings_path()) == expected
    assert glue.settings() == {}
    assert not expected.exists()

    data = {'theme': 'system', 'zoom': 1.2}
    glue.save_settings(data)
    assert expected.is_file()
    assert glue.settings() == data


def test_save_uses_last_loaded_custom_path(tmp_path):
    path = tmp_path / 'prefs.json'
    glue.settings(str(path))
    glue.save_settings({'ok': True})
    assert json.loads(path.read_text(encoding='utf-8')) == {'ok': True}


def test_init_without_app_name_clears_default(tmp_path):
    glue.init(path=tmp_path, app_name='once')
    glue.settings()
    glue.init(path=tmp_path)  # no app_name
    with pytest.raises(RuntimeError, match='app_name'):
        glue.settings()


def test_invalid_app_name(tmp_path):
    with pytest.raises(ValueError):
        glue.init(path=tmp_path, app_name='bad/name')
    with pytest.raises(ValueError):
        glue.init(path=tmp_path, app_name='')
    with pytest.raises(ValueError):
        glue.init(path=tmp_path, app_name='.hidden')


def test_invalid_json_raises(tmp_path):
    path = tmp_path / 'bad.json'
    path.write_text('[]', encoding='utf-8')
    with pytest.raises(TypeError, match='JSON object'):
        glue.settings(str(path))


def test_save_rejects_non_dict(tmp_path):
    with pytest.raises(TypeError):
        glue.save_settings(['nope'], str(tmp_path / 'x.json'))  # type: ignore[arg-type]
