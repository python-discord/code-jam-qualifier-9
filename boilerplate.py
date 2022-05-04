from dataclasses import dataclass
from typing import Awaitable, Callable, Mapping


@dataclass(frozen=True)
class Request:
    scope: Mapping[str, str]

    receive: Callable[[], Awaitable[object]]
    send: Callable[[object], Awaitable[None]]
