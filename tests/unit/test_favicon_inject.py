"""Server-side favicon <link> injection into served HTML."""

from pathlib import Path

import bottle

import glue


def _html(body: str = '') -> str:
    return '<!DOCTYPE html><html><head><title>t</title></head><body>%s</body></html>' % body


def _prepare(tmp_path: Path) -> None:
    glue.init(path=str(tmp_path))
    glue._start_args['disable_cache'] = False


def test_inject_adds_link_when_favicon_exists(tmp_path: Path):
    (tmp_path / 'favicon.ico').write_bytes(b'ICO')
    (tmp_path / 'index.html').write_text(_html(), encoding='utf-8')
    _prepare(tmp_path)

    response = glue._static('index.html')
    text = glue._response_body_text(response)
    assert text is not None
    assert 'rel="icon"' in text
    assert 'href="/favicon.ico?v=' in text
    assert text.index('<head>') < text.index('rel="icon"') < text.index('</head>')


def test_inject_skips_when_icon_link_already_present(tmp_path: Path):
    (tmp_path / 'favicon.ico').write_bytes(b'ICO')
    html = (
        '<!DOCTYPE html><html><head>'
        '<link rel="icon" href="/custom.ico">'
        '<title>t</title></head><body></body></html>'
    )
    (tmp_path / 'index.html').write_text(html, encoding='utf-8')
    _prepare(tmp_path)

    response = glue._static('index.html')
    text = glue._response_body_text(response)
    assert text is not None
    assert text.count('rel="icon"') == 1
    assert '/custom.ico' in text
    assert '/favicon.ico?v=' not in text


def test_inject_noop_without_favicon_file(tmp_path: Path):
    html = _html()
    (tmp_path / 'index.html').write_text(html, encoding='utf-8')
    _prepare(tmp_path)

    response = glue._static('index.html')
    text = glue._response_body_text(response)
    assert text is not None
    assert 'rel="icon"' not in text
    assert text == html


def test_inject_leaves_non_html_untouched(tmp_path: Path):
    (tmp_path / 'favicon.ico').write_bytes(b'ICO')
    css = 'body { color: red; }'
    (tmp_path / 'app.css').write_text(css, encoding='utf-8')
    _prepare(tmp_path)

    response = glue._static('app.css')
    text = glue._response_body_text(response)
    assert text == css


def test_inject_html_favicon_helper_only(tmp_path: Path):
    _prepare(tmp_path)
    html = '<html><head></head></html>'
    assert glue._inject_html_favicon(html) == html

    out = bottle.HTTPResponse(html)
    rebuilt = glue._maybe_inject_favicon_html('index.html', out)
    assert glue._response_body_text(rebuilt) == html
