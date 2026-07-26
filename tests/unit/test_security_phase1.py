import json

import bottle
import pytest

import glue


@pytest.fixture(autouse=True)
def _clean_exposed():
    before = dict(glue._exposed_functions)
    yield
    glue._exposed_functions.clear()
    glue._exposed_functions.update(before)


def test_expose_rejects_invalid_name():
    with pytest.raises(ValueError, match='Invalid JavaScript function name'):
        @glue.expose('bad-name')
        def _fn():
            return None


def test_expose_rejects_duplicate():
    def a():
        return 1

    def b():
        return 2

    glue._expose('phase1_dup_fn', a)
    with pytest.raises(ValueError, match='Already exposed'):
        glue._expose('phase1_dup_fn', b)


def test_expose_accepts_valid_identifier():
    @glue.expose('phase1_ok_fn')
    def phase1_ok_fn():
        return 42

    assert 'phase1_ok_fn' in glue._exposed_functions


def test_glue_js_py_functions_are_json(monkeypatch):
    glue._exposed_functions['phase1_json_fn'] = lambda: None
    glue._start_args.update({
        'size': None,
        'position': None,
        'geometry': {},
        'disable_cache': True,
    })
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
    assert 'phase1_json_fn' in names
    assert '"phase1_json_fn"' in encoded


def test_process_message_omits_traceback(monkeypatch):
    sent = []

    def fake_send(_ws, msg):
        sent.append(json.loads(msg))

    @glue.expose
    def phase1_boom():
        raise RuntimeError('secret path /home/user/x')

    monkeypatch.setattr(glue, '_repeated_send', fake_send)
    glue._process_message(
        {'call': 1, 'name': 'phase1_boom', 'args': []},
        ws=None,
    )
    assert len(sent) == 1
    err = sent[0]['error']
    assert sent[0]['status'] == 'error'
    assert 'errorText' in err
    assert 'errorTraceback' not in err
    assert 'Traceback' not in json.dumps(err)
    assert 'RuntimeError' in err['errorText']


def test_is_loopback_addr():
    assert glue._is_loopback_addr('127.0.0.1')
    assert glue._is_loopback_addr('::1')
    assert glue._is_loopback_addr('localhost')
    assert glue._is_loopback_addr('::ffff:127.0.0.1')
    assert not glue._is_loopback_addr('192.168.1.5')
    assert not glue._is_loopback_addr('10.0.0.1')
    assert not glue._is_loopback_addr(None)
    assert not glue._is_loopback_addr('')
