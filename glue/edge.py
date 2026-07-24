from __future__ import annotations
import os
from shutil import which
from typing import Optional

from glue.chromium import is_windows, run  # shared Chromium launcher API

name: str = 'Microsoft Edge'


def find_path() -> Optional[str]:
    if not is_windows():
        return None
    return _find_edge_win()


def _find_edge_win() -> Optional[str]:
    import winreg as reg

    reg_path = r'SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\msedge.exe'
    for install_type in reg.HKEY_CURRENT_USER, reg.HKEY_LOCAL_MACHINE:
        try:
            reg_key = reg.OpenKey(install_type, reg_path, 0, reg.KEY_READ)
            edge_path = reg.QueryValue(reg_key, None)
            reg_key.Close()
            if edge_path and os.path.isfile(edge_path):
                return edge_path
        except OSError:
            pass

    candidates = [
        os.path.expandvars(r'%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe'),
        os.path.expandvars(r'%ProgramFiles%\Microsoft\Edge\Application\msedge.exe'),
        os.path.expandvars(r'%LocalAppData%\Microsoft\Edge\Application\msedge.exe'),
    ]
    for candidate in candidates:
        if candidate and os.path.isfile(candidate):
            return candidate

    return which('msedge')
