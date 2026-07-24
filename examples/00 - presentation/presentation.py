import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from common import use_shared_assets

import glue

use_shared_assets()
glue.init('web')

PRESENTATION_SIZE = (1920, 1080)


@glue.expose
def get_glue_meta():
    return {
        'name': 'Glue',
        'version': glue.__version__,
    }


@glue.expose
def bridge_echo(payload):
    """Round-trip demo: JS sends a message, Python echoes it with a stamp."""
    text = ''
    if isinstance(payload, dict):
        text = str(payload.get('message', ''))
    else:
        text = str(payload)
    return {
        'ok': True,
        'echo': text,
        'from': 'python',
        'at': datetime.now(timezone.utc).strftime('%H:%M:%S.%f')[:-3] + 'Z',
    }


@glue.expose
def list_simple_steps():
    return [
        {'n': 1, 'code': "glue.init('web')", 'note': 'Serve your HTML/CSS/JS'},
        {'n': 2, 'code': '@glue.expose', 'note': 'Share a Python function'},
        {'n': 3, 'code': "glue.start('index.html')", 'note': 'Open the desktop window'},
    ]


glue.start('index.html', size=PRESENTATION_SIZE)
