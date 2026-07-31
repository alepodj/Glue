"""Private GLFW splash worker.

This module intentionally imports neither Glue nor Bottle. On platforms that
use multiprocessing ``spawn``, keeping the worker's import graph small avoids
loading the application stack a second time before the splash can appear.
"""

from __future__ import annotations

import ctypes
import math
import time
from multiprocessing.connection import Connection
from pathlib import Path
from typing import Any

# OpenGL compatibility constants. A splash only needs one textured rectangle.
GL_BLEND = 0x0BE2
GL_COLOR_BUFFER_BIT = 0x00004000
GL_LINEAR = 0x2601
GL_MODELVIEW = 0x1700
GL_ONE = 1
GL_ONE_MINUS_SRC_ALPHA = 0x0303
GL_PROJECTION = 0x1701
GL_QUADS = 0x0007
GL_RGBA = 0x1908
GL_SRC_ALPHA = 0x0302
GL_TEXTURE_2D = 0x0DE1
GL_TEXTURE_MAG_FILTER = 0x2800
GL_TEXTURE_MIN_FILTER = 0x2801
GL_UNPACK_ALIGNMENT = 0x0CF5
GL_UNSIGNED_BYTE = 0x1401


def _gl_function(glfw: Any, name: str, result_type: Any, *argument_types: Any) -> Any:
    address = glfw.get_proc_address(name)
    if not address:
        raise RuntimeError('OpenGL function is unavailable: %s' % name)
    return ctypes.CFUNCTYPE(result_type, *argument_types)(address)


def _load_gl(glfw: Any) -> dict[str, Any]:
    f32 = ctypes.c_float
    i32 = ctypes.c_int
    u32 = ctypes.c_uint
    return {
        'begin': _gl_function(glfw, 'glBegin', None, u32),
        'bind_texture': _gl_function(glfw, 'glBindTexture', None, u32, u32),
        'blend_func_separate': _gl_function(glfw, 'glBlendFuncSeparate', None, u32, u32, u32, u32),
        'clear': _gl_function(glfw, 'glClear', None, u32),
        'clear_color': _gl_function(glfw, 'glClearColor', None, f32, f32, f32, f32),
        'color': _gl_function(glfw, 'glColor4f', None, f32, f32, f32, f32),
        'delete_textures': _gl_function(glfw, 'glDeleteTextures', None, i32, ctypes.POINTER(u32)),
        'enable': _gl_function(glfw, 'glEnable', None, u32),
        'end': _gl_function(glfw, 'glEnd', None),
        'gen_textures': _gl_function(glfw, 'glGenTextures', None, i32, ctypes.POINTER(u32)),
        'load_identity': _gl_function(glfw, 'glLoadIdentity', None),
        'matrix_mode': _gl_function(glfw, 'glMatrixMode', None, u32),
        'ortho': _gl_function(
            glfw,
            'glOrtho',
            None,
            ctypes.c_double,
            ctypes.c_double,
            ctypes.c_double,
            ctypes.c_double,
            ctypes.c_double,
            ctypes.c_double,
        ),
        'pixel_store': _gl_function(glfw, 'glPixelStorei', None, u32, i32),
        'tex_coord': _gl_function(glfw, 'glTexCoord2f', None, f32, f32),
        'tex_image': _gl_function(
            glfw,
            'glTexImage2D',
            None,
            u32,
            i32,
            i32,
            i32,
            i32,
            i32,
            u32,
            u32,
            ctypes.c_void_p,
        ),
        'tex_parameter': _gl_function(glfw, 'glTexParameteri', None, u32, u32, i32),
        'vertex': _gl_function(glfw, 'glVertex2f', None, f32, f32),
        'viewport': _gl_function(glfw, 'glViewport', None, i32, i32, i32, i32),
    }


def _load_frames(image_path: str) -> tuple[list[tuple[bytes, float]], tuple[int, int]]:
    """Decode PNG/GIF frames into complete RGBA canvases."""
    from PIL import Image  # type: ignore[import-not-found]

    frames: list[tuple[bytes, float]] = []
    with Image.open(Path(image_path)) as image:
        size = image.size
        frame_count = int(getattr(image, 'n_frames', 1))
        for index in range(frame_count):
            image.seek(index)
            if image.size != size:
                raise ValueError('All splash animation frames must use the same dimensions')
            frame = image.convert('RGBA')
            duration_ms = frame.info.get('duration', image.info.get('duration', 100))
            try:
                duration = float(duration_ms) / 1000.0
            except (TypeError, ValueError):
                duration = 0.1
            if not math.isfinite(duration) or duration <= 0:
                duration = 0.1
            # Avoid CPU-burning GIFs with zero/near-zero frame delays.
            frames.append((frame.tobytes(), max(0.02, duration)))
    if not frames:
        raise ValueError('Splash image contains no frames')
    return frames, size


def _create_texture(gl: dict[str, Any], pixels: bytes, size: tuple[int, int]) -> ctypes.c_uint:
    width, height = size
    pixel_buffer = ctypes.create_string_buffer(pixels)
    texture = ctypes.c_uint()
    gl['gen_textures'](1, ctypes.byref(texture))
    gl['bind_texture'](GL_TEXTURE_2D, texture.value)
    gl['tex_parameter'](GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    gl['tex_parameter'](GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    gl['pixel_store'](GL_UNPACK_ALIGNMENT, 1)
    gl['tex_image'](
        GL_TEXTURE_2D,
        0,
        GL_RGBA,
        width,
        height,
        0,
        GL_RGBA,
        GL_UNSIGNED_BYTE,
        ctypes.cast(pixel_buffer, ctypes.c_void_p),
    )
    return texture


def _update_texture(
    gl: dict[str, Any], texture: ctypes.c_uint, pixels: bytes, size: tuple[int, int]
) -> None:
    width, height = size
    pixel_buffer = ctypes.create_string_buffer(pixels)
    gl['bind_texture'](GL_TEXTURE_2D, texture.value)
    gl['tex_image'](
        GL_TEXTURE_2D,
        0,
        GL_RGBA,
        width,
        height,
        0,
        GL_RGBA,
        GL_UNSIGNED_BYTE,
        ctypes.cast(pixel_buffer, ctypes.c_void_p),
    )


def _render(
    gl: dict[str, Any],
    texture: ctypes.c_uint,
    image_size: tuple[int, int],
    framebuffer_size: tuple[int, int],
    opacity: float,
) -> None:
    width, height = image_size
    framebuffer_width, framebuffer_height = framebuffer_size
    gl['viewport'](0, 0, framebuffer_width, framebuffer_height)
    gl['matrix_mode'](GL_PROJECTION)
    gl['load_identity']()
    gl['ortho'](0, width, height, 0, -1, 1)
    gl['matrix_mode'](GL_MODELVIEW)
    gl['load_identity']()

    gl['clear_color'](0.0, 0.0, 0.0, 0.0)
    gl['clear'](GL_COLOR_BUFFER_BIT)
    gl['enable'](GL_BLEND)
    # Preserve source alpha while producing premultiplied RGB for the compositor.
    gl['blend_func_separate'](GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA, GL_ONE, GL_ONE_MINUS_SRC_ALPHA)
    gl['enable'](GL_TEXTURE_2D)
    gl['bind_texture'](GL_TEXTURE_2D, texture.value)
    gl['color'](1.0, 1.0, 1.0, opacity)

    gl['begin'](GL_QUADS)
    gl['tex_coord'](0.0, 0.0)
    gl['vertex'](0.0, 0.0)
    gl['tex_coord'](1.0, 0.0)
    gl['vertex'](width, 0.0)
    gl['tex_coord'](1.0, 1.0)
    gl['vertex'](width, height)
    gl['tex_coord'](0.0, 1.0)
    gl['vertex'](0.0, height)
    gl['end']()


def _center_window(glfw: Any, window: Any, width: int, height: int) -> None:
    monitor = glfw.get_primary_monitor()
    if monitor is None:
        return
    work_area = glfw.get_monitor_workarea(monitor)
    if work_area:
        x, y, work_width, work_height = work_area
    else:
        mode = glfw.get_video_mode(monitor)
        if mode is None:
            return
        x, y, work_width, work_height = 0, 0, mode.size.width, mode.size.height
    glfw.set_window_pos(
        window,
        x + (work_width - width) // 2,
        y + (work_height - height) // 2,
    )


def run_worker(
    connection: Connection,
    image_path: str,
    fade_in: float = 0.45,
    fade_out: float = 0.45,
) -> None:
    """Render the splash until the parent sends ``dismiss`` or ``close``."""
    glfw = None
    window = None
    texture = None
    gl: dict[str, Any] | None = None
    try:
        import glfw as glfw_module  # type: ignore[import-not-found]

        glfw = glfw_module
        # Import and decode before creating a window, so invalid images never flash.
        frames, image_size = _load_frames(image_path)

        errors: list[tuple[int, str]] = []

        def on_error(code: int, message: bytes | str) -> None:
            text = message.decode(errors='replace') if isinstance(message, bytes) else str(message)
            errors.append((code, text))

        glfw.set_error_callback(on_error)
        if not glfw.init():
            raise RuntimeError('GLFW initialization failed: %r' % errors)

        width, height = image_size
        glfw.default_window_hints()
        glfw.window_hint(glfw.DECORATED, glfw.FALSE)
        glfw.window_hint(glfw.RESIZABLE, glfw.FALSE)
        glfw.window_hint(glfw.FLOATING, glfw.TRUE)
        glfw.window_hint(glfw.FOCUSED, glfw.FALSE)
        if hasattr(glfw, 'FOCUS_ON_SHOW'):
            glfw.window_hint(glfw.FOCUS_ON_SHOW, glfw.FALSE)
        glfw.window_hint(glfw.VISIBLE, glfw.FALSE)
        glfw.window_hint(glfw.TRANSPARENT_FRAMEBUFFER, glfw.TRUE)
        glfw.window_hint(glfw.CLIENT_API, glfw.OPENGL_API)
        glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 2)
        glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 1)

        window = glfw.create_window(width, height, 'Glue Splash', None, None)
        if window is None:
            raise RuntimeError('GLFW window creation failed: %r' % errors)
        if not glfw.get_window_attrib(window, glfw.TRANSPARENT_FRAMEBUFFER):
            raise RuntimeError('The desktop compositor did not provide a transparent framebuffer')

        _center_window(glfw, window, width, height)
        glfw.make_context_current(window)
        glfw.swap_interval(1)
        gl = _load_gl(glfw)
        texture = _create_texture(gl, frames[0][0], image_size)

        # Initialize the compositor surface before making the window visible.
        _render(gl, texture, image_size, glfw.get_framebuffer_size(window), 0.0)
        glfw.swap_buffers(window)
        glfw.show_window(window)
        connection.send(('ready', {'size': image_size}))

        started = time.perf_counter()
        dismiss_started: float | None = None
        dismiss_opacity = 1.0
        frame_index = 0
        next_frame = started + frames[0][1]

        while not glfw.window_should_close(window):
            now = time.perf_counter()
            if connection.poll():
                try:
                    command = connection.recv()
                except EOFError:
                    command = 'close'
                if command in ('dismiss', 'close') and dismiss_started is None:
                    dismiss_started = now
                    dismiss_opacity = min(1.0, (now - started) / max(fade_in, 0.001))

            if len(frames) > 1 and now >= next_frame:
                # Advance from deadlines rather than sleeping per frame, skipping
                # overdue frames so animation does not drift.
                while now >= next_frame:
                    frame_index = (frame_index + 1) % len(frames)
                    next_frame += frames[frame_index][1]
                _update_texture(gl, texture, frames[frame_index][0], image_size)

            fade_in_opacity = 1.0 if fade_in <= 0 else min(1.0, (now - started) / fade_in)
            if dismiss_started is None:
                opacity = fade_in_opacity
            elif fade_out <= 0:
                opacity = 0.0
            else:
                opacity = max(
                    0.0,
                    dismiss_opacity * (1.0 - (now - dismiss_started) / fade_out),
                )

            _render(gl, texture, image_size, glfw.get_framebuffer_size(window), opacity)
            glfw.swap_buffers(window)
            glfw.poll_events()
            if dismiss_started is not None and opacity <= 0:
                break
            time.sleep(1 / 120)

        connection.send(('closed', None))
    except Exception as exc:
        try:
            connection.send(('error', '%s: %s' % (type(exc).__name__, exc)))
        except (BrokenPipeError, EOFError, OSError):
            pass
    finally:
        if glfw is not None:
            if window is not None:
                if texture is not None and gl is not None:
                    try:
                        gl['delete_textures'](1, ctypes.byref(texture))
                    except Exception:
                        pass
                glfw.destroy_window(window)
            glfw.terminate()
        connection.close()
