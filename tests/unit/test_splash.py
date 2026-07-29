"""Splash path resolution, timing, lifecycle, and Glue readiness wiring."""

from pathlib import Path

import pytest

import glue
import glue.splash as splash


class FakeConnection:
    def __init__(self, message=('ready', {'size': (64, 64)})):
        self.message = message
        self.sent = []
        self.closed = False

    def poll(self, timeout=None):
        return True

    def recv(self):
        return self.message

    def send(self, message):
        self.sent.append(message)

    def close(self):
        self.closed = True


class FakeProcess:
    def __init__(self):
        self.started = False
        self.alive = False
        self.terminated = False
        self.closed = False

    def start(self):
        self.started = True
        self.alive = True

    def is_alive(self):
        return self.alive

    def join(self, timeout=None):
        if 'dismiss' in getattr(self, 'commands', []):
            self.alive = False

    def terminate(self):
        self.terminated = True
        self.alive = False

    def close(self):
        self.closed = True


class FakeContext:
    def __init__(self, parent=None, child=None, process=None):
        self.parent = parent or FakeConnection()
        self.child = child or FakeConnection()
        self.process = process or FakeProcess()

    def Pipe(self):
        return self.parent, self.child

    def Process(self, **kwargs):
        self.process.commands = self.parent.sent
        return self.process


def test_resolve_true_prefers_ui_png_then_ui_gif_then_project(tmp_path):
    ui = tmp_path / 'ui'
    ui.mkdir()
    project_png = tmp_path / 'splash.png'
    ui_gif = ui / 'splash.gif'
    ui_png = ui / 'splash.png'
    project_png.write_bytes(b'project')
    ui_gif.write_bytes(b'gif')
    ui_png.write_bytes(b'png')

    assert splash.resolve_splash_path(True, ui_root=ui, project_root=tmp_path) == ui_png
    ui_png.unlink()
    assert splash.resolve_splash_path(True, ui_root=ui, project_root=tmp_path) == ui_gif
    ui_gif.unlink()
    assert splash.resolve_splash_path(True, ui_root=ui, project_root=tmp_path) == project_png


def test_resolve_explicit_relative_tries_project_then_ui(tmp_path):
    ui = tmp_path / 'ui'
    ui.mkdir()
    project_image = tmp_path / 'branding' / 'logo.png'
    project_image.parent.mkdir()
    project_image.write_bytes(b'png')
    assert (
        splash.resolve_splash_path(Path('branding/logo.png'), ui_root=ui, project_root=tmp_path)
        == project_image
    )


def test_missing_or_unsupported_image_warns_and_disables(tmp_path):
    ui = tmp_path / 'ui'
    ui.mkdir()
    with pytest.warns(UserWarning, match='not found'):
        assert splash.resolve_splash_path(True, ui_root=ui, project_root=tmp_path) is None

    text = tmp_path / 'splash.svg'
    text.write_text('<svg/>')
    with pytest.warns(UserWarning, match=r'\.png, \.apng, or \.gif'):
        assert splash.resolve_splash_path(text, ui_root=ui, project_root=tmp_path) is None


@pytest.mark.parametrize('value', [0, 0.25, 1, 5.5])
def test_validate_min_duration_accepts_non_negative_finite_numbers(value):
    assert splash.validate_min_duration(value) == float(value)


@pytest.mark.parametrize('value', [-1, float('inf'), float('nan')])
def test_validate_min_duration_rejects_invalid_values(value):
    with pytest.raises(ValueError):
        splash.validate_min_duration(value)


@pytest.mark.parametrize('value', [True, '1', None])
def test_validate_min_duration_rejects_non_numbers(value):
    with pytest.raises(TypeError):
        splash.validate_min_duration(value)


def test_controller_missing_dependencies_is_soft(monkeypatch, tmp_path):
    image = tmp_path / 'splash.png'
    image.write_bytes(b'png')
    monkeypatch.setattr(splash, 'dependencies_available', lambda: False)
    controller = splash.SplashController(image)
    with pytest.warns(UserWarning, match=r'glue-ui\[splash\]'):
        assert controller.start() is False
    assert controller.active is False


def test_controller_starts_and_closes_idempotently(monkeypatch, tmp_path):
    image = tmp_path / 'splash.png'
    image.write_bytes(b'png')
    context = FakeContext()
    monkeypatch.setattr(splash, 'dependencies_available', lambda: True)
    controller = splash.SplashController(image, context=context)

    assert controller.start() is True
    assert context.process.started is True
    controller.close()
    controller.close()
    assert context.process.terminated is True
    assert context.parent.closed is True


def test_minimum_duration_delays_early_readiness(monkeypatch, tmp_path):
    callbacks = []

    class FakeTimer:
        def __init__(self, interval, callback):
            self.interval = interval
            self.callback = callback
            self.daemon = False
            callbacks.append(self)

        def start(self):
            pass

        def cancel(self):
            pass

    image = tmp_path / 'splash.png'
    image.write_bytes(b'png')
    controller = splash.SplashController(image, min_duration=1.0, clock=lambda: 10.25)
    controller._visible_at = 10.0
    sent = []
    monkeypatch.setattr(splash.threading, 'Timer', FakeTimer)
    monkeypatch.setattr(controller, '_send_dismiss', lambda: sent.append('dismiss'))

    controller.dismiss()
    assert callbacks[0].interval == pytest.approx(0.75)
    assert sent == []
    callbacks[0].callback()
    assert sent == ['dismiss']


def test_minimum_duration_dismisses_immediately_when_elapsed(monkeypatch, tmp_path):
    image = tmp_path / 'splash.png'
    image.write_bytes(b'png')
    controller = splash.SplashController(image, min_duration=1.0, clock=lambda: 11.5)
    controller._visible_at = 10.0
    sent = []
    monkeypatch.setattr(controller, '_send_dismiss', lambda: sent.append('dismiss'))
    controller.dismiss()
    assert sent == ['dismiss']


def test_page_ready_only_dismisses_for_initial_page(monkeypatch):
    class Session:
        def __init__(self):
            self.dismissed = 0

        def dismiss(self):
            self.dismissed += 1

    session = Session()
    monkeypatch.setattr(glue, '_splash_session', session)
    monkeypatch.setattr(glue, '_splash_pages', {'index.html'})
    glue._dismiss_splash('other.html')
    glue._dismiss_splash('index.html')
    assert session.dismissed == 1


def test_glue_js_emits_page_ready_event():
    previous = dict(glue._start_args)
    try:
        glue._start_args.update(
            {
                'size': (800, 600),
                'position': None,
                'geometry': {},
                'disable_cache': False,
                'title': None,
            }
        )
        assert "'event': 'page-ready'" in glue._glue()
    finally:
        glue._start_args.clear()
        glue._start_args.update(previous)
