from typing import Callable, TypeVar

C = TypeVar('C', bound=Callable)


def step(number: int, *, optional: bool = False) -> Callable[[C], C]:
    def decorator(func: C) -> C:
        func._step_num = number
        func._optional_test = optional
        return func
    return decorator
