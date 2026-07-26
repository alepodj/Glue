from __future__ import annotations
import sys
from shutil import which
from typing import Optional

from glue.browsers_launcher import (
    find_app_path_win,
    find_mac_app,
    is_windows,
    run,
)

name: str = 'Google Chrome/Chromium'


def find_path() -> Optional[str]:
    if is_windows():
        return find_app_path_win('chrome.exe')
    if sys.platform == 'darwin':
        return (
            find_mac_app('Google Chrome.app', 'Google Chrome')
            or find_mac_app('Chromium.app', 'Chromium')
        )
    if sys.platform.startswith('linux'):
        return _find_chrome_linux()
    return None


def _find_chrome_linux() -> Optional[str]:
    for binary in (
        'chromium-browser',
        'chromium',
        'google-chrome',
        'google-chrome-stable',
    ):
        path = which(binary)
        if path is not None:
            return path
    return None
