"""Security: glue.js encoding, RPC error shape, loopback checks."""

import json

import bottle
import pytest

import glue
import glue.webview as webview


@pytest.fixture(autouse=True)
def _clean_exposed():
    before = dict(glue._exposed_functions)
    yield
    glue._exposed_functions.clear()
    glue._exposed_functions.update(before)


def test_glue_js_py_functions_are_json(monkeypatch):
    glue._exposed_functions['json_fn'] = lambda: None
    w, h = webview.DEFAULT_WINDOW_SIZE
    glue._start_args.update(
        {
            'size': (w, h),
            'position': None,
            'geometry': {},
            'disable_cache': True,
        }
    )
    monkeypatch.setattr(glue, '_set_response_headers', lambda _r: None)

    environ = {
        'REQUEST_METHOD': 'GET',
        'PATH_INFO': '/glue.js',
        'SERVER_PROTOCOL': 'HTTP/1.1',
        'HTTP_HOST': 'localhost',
        'wsgi.url_scheme': 'http',
    }
    bottle.request.bind(environ)
    bottle.response.bind()
    try:
        body = glue._glue()
    finally:
        bottle.request.bind({})

    marker = '_py_functions: '
    assert marker in body
    start = body.index(marker) + len(marker)
    end = body.index(',', start)
    encoded = body[start:end]
    names = json.loads(encoded)
    assert isinstance(names, list)
    assert 'json_fn' in names
    assert '"json_fn"' in encoded


def test_process_message_omits_traceback(monkeypatch):
    sent = []

    def fake_send(_ws, msg):
        sent.append(json.loads(msg))

    @glue.expose
    def boom():
        raise RuntimeError('secret path /home/user/x')

    monkeypatch.setattr(glue, '_repeated_send', fake_send)
    glue._process_message({'call': 1, 'name': 'boom', 'args': []}, ws=None)
    assert len(sent) == 1
    err = sent[0]['error']
    assert sent[0]['status'] == 'error'
    assert 'errorText' in err
    assert 'errorTraceback' not in err
    assert 'Traceback' not in json.dumps(err)
    assert 'RuntimeError' in err['errorText']


def test_process_message_success(monkeypatch):
    sent = []

    def fake_send(_ws, msg):
        sent.append(json.loads(msg))

    @glue.expose
    def add(a, b):
        return a + b

    monkeypatch.setattr(glue, '_repeated_send', fake_send)
    glue._process_message({'call': 2, 'name': 'add', 'args': [2, 3]}, ws=None)
    assert len(sent) == 1
    assert sent[0]['status'] == 'ok'
    assert sent[0]['return'] == 2
    assert sent[0]['value'] == 5


def test_process_message_unknown_name(monkeypatch):
    sent = []

    def fake_send(_ws, msg):
        sent.append(json.loads(msg))

    monkeypatch.setattr(glue, '_repeated_send', fake_send)
    glue._process_message({'call': 3, 'name': 'missing_fn', 'args': []}, ws=None)
    assert len(sent) == 1
    assert sent[0]['status'] == 'error'
    assert 'errorText' in sent[0]['error']


def test_is_loopback_addr():
    assert glue._is_loopback_addr('127.0.0.1')
    assert glue._is_loopback_addr('::1')
    assert glue._is_loopback_addr('localhost')
    assert glue._is_loopback_addr('::ffff:127.0.0.1')
    assert not glue._is_loopback_addr('192.168.1.5')
    assert not glue._is_loopback_addr('10.0.0.1')
    assert not glue._is_loopback_addr(None)
    assert not glue._is_loopback_addr('')
