"""Optional GLFW splash support for Glue applications."""

from __future__ import annotations

import importlib.util
import math
import multiprocessing
import os
import threading
import time
import warnings
from os import PathLike
from pathlib import Path
from typing import Any

from glue._splash_worker import run_worker

SplashValue = bool | str | PathLike[str]
_SUPPORTED_EXTENSIONS = {'.apng', '.gif', '.png'}


def validate_min_duration(value: int | float) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError("'splash_min_duration' must be a non-negative number")
    duration = float(value)
    if not math.isfinite(duration) or duration < 0:
        raise ValueError("'splash_min_duration' must be a finite, non-negative number")
    return duration


def resolve_splash_path(
    splash: SplashValue,
    *,
    ui_root: str | os.PathLike[str],
    project_root: str | os.PathLike[str] | None = None,
) -> Path | None:
    """Resolve an explicit splash or discover a PNG/APNG/GIF named ``splash``."""
    ui_path = Path(ui_root).resolve()
    project_path = Path(project_root or os.getcwd()).resolve()

    if splash is False:
        return None
    candidates: tuple[Path, ...]
    if splash is True:
        candidates = (
            ui_path / 'splash.png',
            ui_path / 'splash.apng',
            ui_path / 'splash.gif',
            project_path / 'splash.png',
            project_path / 'splash.apng',
            project_path / 'splash.gif',
        )
    elif isinstance(splash, (str, os.PathLike)):
        supplied = Path(splash)
        candidates = (
            (supplied,)
            if supplied.is_absolute()
            else (
                project_path / supplied,
                ui_path / supplied,
            )
        )
    else:
        raise TypeError("'splash' must be False, True, or a filesystem path")

    for candidate in candidates:
        if candidate.is_file():
            resolved = candidate.resolve()
            if resolved.suffix.lower() not in _SUPPORTED_EXTENSIONS:
                warnings.warn(
                    'Splash images must use .png, .apng, or .gif: %s' % resolved,
                    UserWarning,
                    stacklevel=2,
                )
                return None
            return resolved

    warnings.warn(
        'Splash image not found; continuing without splash. Searched: %s'
        % ', '.join(str(candidate) for candidate in candidates),
        UserWarning,
        stacklevel=2,
    )
    return None


def dependencies_available() -> bool:
    return (
        importlib.util.find_spec('glfw') is not None and importlib.util.find_spec('PIL') is not None
    )


class SplashController:
    """Own one splash worker and its full lifecycle."""

    def __init__(
        self,
        image_path: str | os.PathLike[str],
        *,
        min_duration: float = 1.0,
        startup_timeout: float = 10.0,
        maximum_duration: float = 30.0,
        context: Any = None,
        clock: Any = time.monotonic,
    ) -> None:
        self.image_path = str(Path(image_path).resolve())
        self.min_duration = validate_min_duration(min_duration)
        self.startup_timeout = float(startup_timeout)
        self.maximum_duration = float(maximum_duration)
        self._context = context
        self._clock = clock
        self._connection: Any = None
        self._process: Any = None
        self._visible_at: float | None = None
        self._dismiss_requested = False
        self._closed = False
        self._dismiss_timer: threading.Timer | None = None
        self._maximum_timer: threading.Timer | None = None
        self._lock = threading.RLock()

    @property
    def active(self) -> bool:
        process = self._process
        return bool(
            not self._closed
            and process is not None
            and getattr(process, 'is_alive', lambda: False)()
        )

    def start(self) -> bool:
        """Start and wait until the transparent window has been presented."""
        with self._lock:
            if self._process is not None:
                return self.active
            if not dependencies_available():
                warnings.warn(
                    'Splash support requires optional dependencies. Install with: '
                    'pip install "glue-ui[splash]". Continuing without splash.',
                    UserWarning,
                    stacklevel=2,
                )
                self._closed = True
                return False

            context = self._context or multiprocessing.get_context('spawn')
            parent_connection, child_connection = context.Pipe()
            process = context.Process(
                target=run_worker,
                args=(child_connection, self.image_path),
                name='glue-splash',
                daemon=True,
            )
            self._connection = parent_connection
            self._process = process

        try:
            process.start()
            child_connection.close()
            if not parent_connection.poll(self.startup_timeout):
                raise TimeoutError('splash worker did not become ready')
            message_type, payload = parent_connection.recv()
            if message_type != 'ready':
                raise RuntimeError(payload or 'splash worker failed before readiness')
        except Exception as exc:
            try:
                child_connection.close()
            except Exception:
                pass
            warnings.warn(
                'Could not start splash (%s); continuing without it.' % exc,
                UserWarning,
                stacklevel=2,
            )
            self.close()
            return False

        with self._lock:
            self._visible_at = self._clock()
            self._maximum_timer = threading.Timer(self.maximum_duration, self.dismiss)
            self._maximum_timer.daemon = True
            self._maximum_timer.start()
        return True

    def dismiss(self) -> None:
        """Fade out once the configured minimum display time has elapsed."""
        with self._lock:
            if self._closed or self._dismiss_requested or self._visible_at is None:
                return
            self._dismiss_requested = True
            remaining = self.min_duration - (self._clock() - self._visible_at)
            if remaining > 0:
                self._dismiss_timer = threading.Timer(remaining, self._send_dismiss)
                self._dismiss_timer.daemon = True
                self._dismiss_timer.start()
                return
        self._send_dismiss()

    def _send_dismiss(self) -> None:
        with self._lock:
            if self._closed:
                return
            try:
                self._connection.send('dismiss')
            except (BrokenPipeError, EOFError, OSError):
                pass
            reaper = threading.Thread(target=self._reap, name='glue-splash-reaper', daemon=True)
            reaper.start()

    def _reap(self) -> None:
        process = self._process
        if process is not None:
            process.join(timeout=3.0)
        self.close()

    def close(self) -> None:
        """Close immediately. Safe after partial startup and safe to repeat."""
        with self._lock:
            if self._closed:
                return
            self._closed = True
            for timer in (self._dismiss_timer, self._maximum_timer):
                if timer is not None:
                    timer.cancel()
            connection = self._connection
            process = self._process

        if connection is not None:
            try:
                connection.send('close')
            except (BrokenPipeError, EOFError, OSError):
                pass
        if process is not None:
            try:
                process.join(timeout=0.75)
                if process.is_alive():
                    process.terminate()
                    process.join(timeout=1.0)
            except (AssertionError, OSError, ValueError):
                pass
        if connection is not None:
            try:
                connection.close()
            except OSError:
                pass
        if process is not None:
            try:
                process.close()
            except (OSError, ValueError):
                pass


def start_splash(
    splash: SplashValue,
    *,
    ui_root: str | os.PathLike[str],
    min_duration: int | float = 1.0,
    project_root: str | os.PathLike[str] | None = None,
) -> SplashController | None:
    duration = validate_min_duration(min_duration)
    path = resolve_splash_path(splash, ui_root=ui_root, project_root=project_root)
    if path is None:
        return None
    controller = SplashController(path, min_duration=duration)
    return controller if controller.start() else None
