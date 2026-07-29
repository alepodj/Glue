from __future__ import annotations

import os
from argparse import ArgumentParser, Namespace
from importlib.resources import as_file, files

try:
    import PyInstaller.__main__ as pyi
except ImportError as exc:
    raise SystemExit(
        "PyInstaller is required for `python -m glue`. Install with: pip install 'glue-ui[build]'"
    ) from exc

parser: ArgumentParser = ArgumentParser(
    description="""
Glue is a little Python library for making simple desktop HTML/JS GUI apps
(PyWebView by default, with Chrome/Edge fallback), with full access to Python
capabilities and libraries.
"""
)
parser.add_argument('main_script', type=str, help='Main python file to run app from')
parser.add_argument(
    'ui_folder',
    type=str,
    help="Folder with frontend files (html, css, js, icons, …); typically 'ui'",
)
args: Namespace
unknown_args: list[str]
args, unknown_args = parser.parse_known_args()
main_script: str = args.main_script
ui_folder: str = args.ui_folder

print(
    "Building executable with main script '%s' and UI folder '%s'...\n" % (main_script, ui_folder)
)

_glue_js_ref = files('glue') / 'glue.js'
with as_file(_glue_js_ref) as _glue_js_path:
    glue_js_file: str = str(_glue_js_path)
    js_file_arg: str = '%s%sglue' % (glue_js_file, os.pathsep)
    ui_folder_arg: str = '%s%s%s' % (ui_folder, os.pathsep, ui_folder)

    needed_args: list[str] = [
        '--hidden-import',
        'bottle_websocket',
        '--add-data',
        js_file_arg,
        '--add-data',
        ui_folder_arg,
    ]
    full_args: list[str] = [main_script] + needed_args + unknown_args
    print('Running:\npyinstaller', ' '.join(full_args), '\n')

    pyi.run(full_args)
