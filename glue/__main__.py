from __future__ import annotations
import os
from argparse import ArgumentParser, Namespace
from typing import List

import importlib_resources

try:
    import PyInstaller.__main__ as pyi
except ImportError as exc:
    raise SystemExit(
        "PyInstaller is required for `python -m glue`. "
        "Install with: pip install 'Glue[build]'"
    ) from exc

parser: ArgumentParser = ArgumentParser(description="""
Glue is a little Python library for making simple Chromium-based offline HTML/JS GUI apps,
 with full access to Python capabilities and libraries.
""")
parser.add_argument(
    "main_script",
    type=str,
    help="Main python file to run app from"
)
parser.add_argument(
    "web_folder",
    type=str,
    help="Folder including all web files including file as html, css, ico, etc."
)
args: Namespace
unknown_args: List[str]
args, unknown_args = parser.parse_known_args()
main_script: str = args.main_script
web_folder: str = args.web_folder

print("Building executable with main script '%s' and web folder '%s'...\n" %
      (main_script, web_folder))

_glue_js_ref = importlib_resources.files('glue') / 'glue.js'
with importlib_resources.as_file(_glue_js_ref) as _glue_js_path:
    glue_js_file: str = str(_glue_js_path)
    js_file_arg: str = '%s%sglue' % (glue_js_file, os.pathsep)
    web_folder_arg: str = '%s%s%s' % (web_folder, os.pathsep, web_folder)

    needed_args: List[str] = ['--hidden-import', 'bottle_websocket',
                              '--add-data', js_file_arg, '--add-data', web_folder_arg]
    full_args: List[str] = [main_script] + needed_args + unknown_args
    print('Running:\npyinstaller', ' '.join(full_args), '\n')

    pyi.run(full_args)
