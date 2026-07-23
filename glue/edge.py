from __future__ import annotations
import os
import platform
import subprocess as sps
import sys
from shutil import which
from typing import List, Optional

from glue.types import OptionsDictT

name: str = 'Microsoft Edge'


def run(path: str, options: OptionsDictT, start_urls: List[str]) -> None:
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


def find_path() -> Optional[str]:
    if platform.system() != 'Windows':
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
