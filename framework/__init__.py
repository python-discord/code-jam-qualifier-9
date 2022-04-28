from dataclasses import dataclass
from typing import Any, Awaitable, Callable


@dataclass
class Request:
    scope: dict[str, Any]
    receive: Callable[[], Awaitable[object]]
    send: Callable[[object], Awaitable[None]]
