from datetime import datetime, timezone

import glue

glue.init('web')

PRESENTATION_SIZE = (1920, 1080)


@glue.expose
def get_glue_meta():
    return {
        'name': 'Glue',
        'version': glue.__version__,
    }


def _payload_text(payload):
    if isinstance(payload, dict):
        return str(payload.get('message', ''))
    return str(payload)


def _stamp():
    return datetime.now(timezone.utc).strftime('%H:%M:%S.%f')[:-3] + 'Z'


@glue.expose
def bridge_echo(payload):
    """JS -> Python: echo a message with a stamp."""
    return {
        'ok': True,
        'echo': _payload_text(payload),
        'from': 'python',
        'at': _stamp(),
    }


@glue.expose
def bridge_call_js(payload):
    """Python -> JS: call an exposed JavaScript function and return its reply."""
    text = _payload_text(payload) or 'hello from Python'
    js_reply = glue.bridge_on_js({'message': text, 'from': 'python'})()
    return {
        'ok': True,
        'sent': text,
        'js_reply': js_reply,
        'from': 'python',
        'at': _stamp(),
    }


glue.start('index.html', size=PRESENTATION_SIZE)
