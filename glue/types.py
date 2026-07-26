from __future__ import annotations
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Tuple,
    TypeAlias,
    TypedDict,
    Union,
    TYPE_CHECKING,
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
    size: Optional[Tuple[int, int]]
    position: Optional[Tuple[int, int]]


OptionsDictT = TypedDict(
    'OptionsDictT',
    {
        'mode': Optional[str],
        'host': str,
        'port': int,
        'block': bool,
        'jinja_templates': Optional[str],
        'cmdline_args': List[str],
        'size': Optional[Tuple[int, int]],
        'position': Optional[Tuple[int, int]],
        'geometry': Dict[str, WindowGeometryT],
        'close_callback': Optional[Callable[..., Any]],
        'app_mode': bool,
        'all_interfaces': bool,
        'disable_cache': bool,
        'default_path': str,
        'app': Bottle,
        'shutdown_delay': float,
        'jinja_env': JinjaEnvironmentT,
        'title': Optional[str],
        'resizable': bool,
        'webview_options': Dict[str, Any],
    },
    total=False
)
