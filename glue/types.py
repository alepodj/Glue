from __future__ import annotations

from collections.abc import Callable
from typing import (
    TYPE_CHECKING,
    Any,
    TypeAlias,
    TypedDict,
)

from bottle import Bottle

# jinja2 may be optional at runtime; geventwebsocket.websocket has no type stubs.
if TYPE_CHECKING:
    from jinja2 import Environment

    JinjaEnvironmentT: TypeAlias = Environment
    from geventwebsocket.websocket import WebSocket

    WebSocketT: TypeAlias = WebSocket
else:
    JinjaEnvironmentT: TypeAlias = Any
    WebSocketT: TypeAlias = Any


class WindowGeometryT(TypedDict, total=False):
    size: tuple[int, int] | None
    position: tuple[int, int] | None


class OptionsDictT(TypedDict, total=False):
    mode: str | None
    host: str
    port: int
    block: bool
    jinja_templates: str | None
    cmdline_args: list[str]
    size: tuple[int, int] | None
    position: tuple[int, int] | None
    geometry: dict[str, WindowGeometryT]
    close_callback: Callable[..., Any] | None
    app_mode: bool
    all_interfaces: bool
    disable_cache: bool
    default_path: str
    app: Bottle
    shutdown_delay: float
    jinja_env: JinjaEnvironmentT
    title: str | None
    resizable: bool
    webview_options: dict[str, Any]
