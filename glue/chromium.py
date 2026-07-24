from __future__ import annotations
import subprocess as sps
import sys
from typing import List

from glue.types import OptionsDictT


def run(path: str, options: OptionsDictT, start_urls: List[str]) -> None:
    """Launch a Chromium-based browser (Chrome, Edge, Chromium, …)."""
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
