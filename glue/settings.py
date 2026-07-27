"""User settings JSON under ``~/.{app_name}/{app_name}.json`` (opt-in via app_name)."""

from __future__ import annotations

import json
import os
import re
import tempfile
from pathlib import Path
from typing import Any

JsonDict = dict[str, Any]

_APP_NAME_RE = re.compile(r'^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$')

_app_name: str | None = None
_last_path: Path | None = None


def configure(app_name: str | None = None) -> None:
    """Set or clear the opt-in app name used for the default settings path."""
    global _app_name, _last_path
    if app_name is None:
        _app_name = None
        _last_path = None
        return
    if not isinstance(app_name, str):
        raise TypeError('app_name must be a string')
    name = app_name.strip()
    if not name or not _APP_NAME_RE.match(name):
        raise ValueError(
            "app_name must be 1–64 chars: letters, digits, '.', '_', or '-'; "
            'and must start with a letter or digit (got %r)' % (app_name,)
        )
    if _app_name != name:
        _last_path = None
    _app_name = name


def app_name() -> str | None:
    return _app_name


def default_path() -> Path:
    """Resolved ``~/.{app_name}/{app_name}.json``. Requires ``app_name``."""
    if not _app_name:
        raise RuntimeError(
            'No default settings path: pass app_name to glue.init() '
            "(e.g. glue.init(app_name='myapp')), or pass an explicit path to "
            'glue.settings(path) / glue.save_settings(data, path).'
        )
    return Path.home() / ('.' + _app_name) / (_app_name + '.json')


def settings_path() -> Path:
    """Alias for :func:`default_path`."""
    return default_path()


def _resolve_path(path: str | Path | None = None) -> Path:
    if path is None:
        return default_path()
    return Path(path).expanduser().resolve()


def load(path: str | Path | None = None) -> JsonDict:
    """Load settings JSON.

    With no *path*, uses the default location (requires ``app_name``).
    Missing file → ``{}``. Does not create directories or files.
    """
    global _last_path
    resolved = _resolve_path(path)
    _last_path = resolved
    if not resolved.is_file():
        return {}
    with open(resolved, encoding='utf-8') as fh:
        data = json.load(fh)
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise TypeError(
            'Settings file must contain a JSON object (got %s): %s'
            % (type(data).__name__, resolved)
        )
    return data


def save(data: JsonDict, path: str | Path | None = None) -> Path:
    """Write *data* as JSON. Creates parent dirs. Atomic replace.

    With no *path*, writes to the last path from :func:`load`, or the default
    path when ``app_name`` is set.
    """
    global _last_path
    if not isinstance(data, dict):
        raise TypeError('settings data must be a dict, got %s' % type(data).__name__)

    if path is not None:
        resolved = _resolve_path(path)
    elif _last_path is not None:
        resolved = _last_path
    else:
        resolved = default_path()

    resolved.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(data, indent=2, ensure_ascii=False) + '\n'
    fd, tmp_name = tempfile.mkstemp(
        prefix=resolved.name + '.',
        suffix='.tmp',
        dir=str(resolved.parent),
    )
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as fh:
            fh.write(payload)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp_name, resolved)
    except Exception:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise

    _last_path = resolved
    return resolved


def reset() -> None:
    """Clear module state (tests)."""
    global _app_name, _last_path
    _app_name = None
    _last_path = None
