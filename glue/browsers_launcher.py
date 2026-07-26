from __future__ import annotations
import os
import subprocess as sps
import sys
from typing import List, Optional

from glue.types import OptionsDictT


def run(path: str, options: OptionsDictT, start_urls: List[str]) -> None:
    """Launch a Chromium-family browser binary (Chrome, Edge, Chromium, …).

    Shared by :mod:`glue.chrome` and :mod:`glue.edge`. Orchestration lives in
    :mod:`glue.browsers`.
    """
    if not isinstance(options['cmdline_args'], list):
        raise TypeError("'cmdline_args' option must be of type List[str]")
    if options['app_mode']:
        for url in start_urls:
            sps.Popen([path, '--app=%s' % url] +
                      options['cmdline_args'],
                      stdout=sps.PIPE, stderr=sps.PIPE, stdin=sps.PIPE)
    else:
        args: List[str] = options['cmdline_args'] + start_urls
        sps.Popen([path, '--new-window'] + args,
                  stdout=sps.PIPE, stderr=sys.stderr, stdin=sps.PIPE)


def is_windows() -> bool:
    """True on CPython Windows (`sys.platform` is always ``win32`` there)."""
    return sys.platform == 'win32' or sys.platform.startswith('win')


def platform_name() -> str:
    """Return ``windows``, ``macos``, or ``linux`` for host/UI styling."""
    if sys.platform == 'darwin':
        return 'macos'
    if is_windows():
        return 'windows'
    return 'linux'


def find_app_path_win(exe_name: str) -> Optional[str]:
    """Resolve an executable via HKCU/HKLM ``App Paths`` (Windows only).

    *exe_name* is the registry leaf, e.g. ``chrome.exe`` or ``msedge.exe``.
    """
    if not is_windows():
        return None
    import winreg as reg

    reg_path = r'SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\%s' % exe_name
    for install_type in reg.HKEY_CURRENT_USER, reg.HKEY_LOCAL_MACHINE:
        try:
            reg_key = reg.OpenKey(install_type, reg_path, 0, reg.KEY_READ)
            path = reg.QueryValue(reg_key, None)
            reg_key.Close()
            if path and os.path.isfile(path):
                return path
        except OSError:
            pass
    return None


def find_mac_app(app_bundle: str, binary_name: str) -> Optional[str]:
    """Locate a macOS ``.app`` binary under ``/Applications`` or via ``mdfind``."""
    default = '/Applications/%s/Contents/MacOS/%s' % (app_bundle, binary_name)
    if os.path.exists(default):
        return default
    try:
        matches = [
            line for line in sps.check_output(['mdfind', app_bundle]).decode().split('\n')
            if line.endswith(app_bundle)
        ]
    except (OSError, sps.CalledProcessError):
        return None
    if matches:
        return matches[0] + '/Contents/MacOS/' + binary_name
    return None
