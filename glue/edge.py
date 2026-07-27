from __future__ import annotations

import os
from shutil import which

from glue.browsers_launcher import find_app_path_win, is_windows

name: str = 'Microsoft Edge'


def find_path() -> str | None:
    if not is_windows():
        return None
    return _find_edge_win()


def _find_edge_win() -> str | None:
    path = find_app_path_win('msedge.exe')
    if path:
        return path

    candidates = [
        os.path.expandvars(r'%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe'),
        os.path.expandvars(r'%ProgramFiles%\Microsoft\Edge\Application\msedge.exe'),
        os.path.expandvars(r'%LocalAppData%\Microsoft\Edge\Application\msedge.exe'),
    ]
    for candidate in candidates:
        if candidate and os.path.isfile(candidate):
            return candidate

    return which('msedge')
