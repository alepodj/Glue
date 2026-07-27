"""HTTP routes, cache headers, and start() size default."""

import bottle
import pytest

import glue
import glue.webview as webview


def test_register_glue_routes():
    app = bottle.Bottle()
    glue.register_glue_routes(app)
    rules = {route.rule for route in app.routes}
    assert '/glue.js' in rules
    assert '/' in rules
    assert '/glue' in rules
    assert '/<path:path>' in rules


def test_disable_cache_sets_header():
    prev = dict(glue._start_args)
    try:
        glue._start_args['disable_cache'] = True
        response = bottle.HTTPResponse()
        glue._set_response_headers(response)
        assert response.get_header('Cache-Control') == 'no-store'

        glue._start_args['disable_cache'] = False
        response2 = bottle.HTTPResponse()
        glue._set_response_headers(response2)
        assert response2.get_header('Cache-Control') is None
    finally:
        glue._start_args.clear()
        glue._start_args.update(prev)


def test_start_resolves_default_size(monkeypatch, tmp_path):
    (tmp_path / 'index.html').write_text('<html></html>', encoding='utf-8')
    glue.init(path=str(tmp_path))

    seen = {}

    def stop_after_args(*_args, **_kwargs):
        seen['size'] = glue._start_args.get('size')
        raise RuntimeError('stop-after-start-args')

    # mode=None uses spawn(run_lambda) after _start_args is filled.
    monkeypatch.setattr(glue, 'spawn', stop_after_args)
    with pytest.raises(RuntimeError, match='stop-after-start-args'):
        glue.start('index.html', mode=None, block=False, size=None)

    assert seen['size'] == webview.DEFAULT_WINDOW_SIZE
