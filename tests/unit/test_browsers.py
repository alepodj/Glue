"""Window host selection: auto / webview / chrome / edge / custom / None."""

import pytest

import glue.browsers as browsers
import glue.browsers_launcher as browsers_launcher


def test_build_urls_from_string_and_dict():
    options = {'host': '127.0.0.1', 'port': 9000}
    urls = browsers._build_urls(
        ['hello.html', {'path': 'other.html', 'host': 'localhost', 'port': '9001'}],
        options,
    )
    assert urls == [
        'http://127.0.0.1:9000/hello.html',
        'http://localhost:9001/other.html',
    ]


def test_auto_browser_order(monkeypatch):
    monkeypatch.setattr(browsers, 'is_windows', lambda: True)
    assert browsers._auto_browser_order() == ['chrome', 'edge']
    monkeypatch.setattr(browsers, 'is_windows', lambda: False)
    assert browsers._auto_browser_order() == ['chrome']


def test_auto_tries_webview_before_browsers(monkeypatch):
    calls = []

    monkeypatch.setattr(browsers.webview, 'should_try', lambda _opts: True)

    def fake_webview(options, start_urls, *, required):
        calls.append(('webview', required))
        browsers._webview_session_completed = True
        return 'completed'

    def boom(*_a, **_k):
        raise AssertionError('browser should not launch when webview succeeds')

    monkeypatch.setattr(browsers, '_open_webview', fake_webview)
    monkeypatch.setattr(browsers, '_run_browser', boom)
    browsers.open(
        ['index.html'],
        {'mode': 'auto', 'host': 'localhost', 'port': 8000, 'block': True},
    )
    assert calls == [('webview', False)]
    assert browsers.webview_session_completed() is True


def test_auto_falls_back_when_webview_unavailable(monkeypatch):
    calls = []

    monkeypatch.setattr(browsers.webview, 'should_try', lambda _opts: True)
    monkeypatch.setattr(browsers, '_open_webview', lambda *_a, **_k: 'unavailable')
    monkeypatch.setattr(browsers, 'is_windows', lambda: True)

    def fake_run(name, options, start_urls):
        calls.append(name)
        return name == 'chrome'

    monkeypatch.setattr(browsers, '_run_browser', fake_run)
    browsers.open(
        ['index.html'],
        {'mode': 'auto', 'host': 'localhost', 'port': 8000, 'block': True},
    )
    assert calls == ['chrome']


def test_auto_skips_webview_when_not_blocking(monkeypatch):
    calls = []

    def boom_webview(*_a, **_k):
        raise AssertionError('webview should be skipped when block=False')

    monkeypatch.setattr(browsers.webview, 'should_try', lambda opts: False)
    monkeypatch.setattr(browsers, '_open_webview', boom_webview)
    monkeypatch.setattr(browsers, 'is_windows', lambda: False)

    def fake_run(name, options, start_urls):
        calls.append(name)
        return True

    monkeypatch.setattr(browsers, '_run_browser', fake_run)
    browsers.open(
        ['index.html'],
        {'mode': 'auto', 'host': 'localhost', 'port': 8000, 'block': False},
    )
    assert calls == ['chrome']


def test_webview_mode_requires_block(monkeypatch):
    monkeypatch.setattr(browsers.webview, 'available', lambda: True)
    with pytest.raises(ValueError, match='block=True'):
        browsers.open(
            ['index.html'],
            {'mode': 'webview', 'host': 'localhost', 'port': 8000, 'block': False},
        )


def test_open_mode_none_does_not_launch(monkeypatch):
    launched = []

    def boom(*_a, **_k):
        launched.append(True)
        raise AssertionError('browser should not launch')

    monkeypatch.setattr(browsers, '_open_auto', boom)
    monkeypatch.setattr(browsers, '_run_browser', boom)
    monkeypatch.setattr(browsers, '_open_webview', boom)
    browsers.open(['index.html'], {'mode': None, 'host': 'localhost', 'port': 8000})
    assert launched == []


def test_open_unsupported_mode():
    with pytest.raises(ValueError, match='Unsupported mode'):
        browsers.open(
            ['index.html'],
            {'mode': 'firefox', 'host': 'localhost', 'port': 8000},
        )


@pytest.mark.parametrize('mode', ['chrome', 'edge'])
def test_open_chrome_or_edge_uses_run_browser(monkeypatch, mode):
    calls = []

    def fake_run(name, options, start_urls):
        calls.append((name, start_urls))
        return True

    monkeypatch.setattr(browsers, '_run_browser', fake_run)
    browsers.open(
        ['index.html'],
        {'mode': mode, 'host': 'localhost', 'port': 8000},
    )
    assert calls == [(mode, ['http://localhost:8000/index.html'])]


@pytest.mark.parametrize('browser_name', ['chrome', 'edge'])
def test_run_browser_uses_launcher_not_module_run(monkeypatch, browser_name):
    """chrome/edge only find_path; launch must go through browsers_launcher.run."""
    launched = []

    monkeypatch.setattr(
        browsers,
        '_resolved_path',
        lambda name: r'C:\fake\%s.exe' % name if name == browser_name else None,
    )

    def fake_launcher_run(path, options, start_urls):
        launched.append((path, list(start_urls)))

    monkeypatch.setattr(browsers_launcher, 'run', fake_launcher_run)
    assert browsers._run_browser(
        browser_name,
        {'cmdline_args': [], 'app_mode': True},
        ['http://localhost:8000/index.html'],
    )
    assert launched == [
        (r'C:\fake\%s.exe' % browser_name, ['http://localhost:8000/index.html'])
    ]
    assert not hasattr(browsers._browser_modules[browser_name], 'run')


def test_run_browser_missing_binary(monkeypatch):
    monkeypatch.setattr(browsers, '_resolved_path', lambda _name: None)
    assert (
        browsers._run_browser(
            'chrome',
            {'cmdline_args': [], 'app_mode': True},
            ['http://localhost:8000/'],
        )
        is False
    )


def test_open_custom_uses_popen(monkeypatch):
    calls = []

    class FakePopen:
        def __init__(self, args, **_kwargs):
            calls.append(args)

    monkeypatch.setattr(browsers.sps, 'Popen', FakePopen)
    browsers.open(
        ['index.html'],
        {
            'mode': 'custom',
            'host': 'localhost',
            'port': 8000,
            'cmdline_args': ['my-browser', '--app=http://x'],
        },
    )
    assert calls == [['my-browser', '--app=http://x']]


def test_platform_name(monkeypatch):
    monkeypatch.setattr(browsers_launcher.sys, 'platform', 'win32')
    assert browsers_launcher.platform_name() == 'windows'
    monkeypatch.setattr(browsers_launcher.sys, 'platform', 'darwin')
    assert browsers_launcher.platform_name() == 'macos'
    monkeypatch.setattr(browsers_launcher.sys, 'platform', 'linux')
    assert browsers_launcher.platform_name() == 'linux'
