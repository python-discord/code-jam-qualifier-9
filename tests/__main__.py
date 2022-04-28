import asyncio
import os
import sys
from importlib import import_module
from types import ModuleType
from typing import Callable


async def run_tests(tests) -> int:
    tasks = {asyncio.create_task(test()): test for test in tests}
    done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_EXCEPTION)

    for task in pending:
        task.cancel()

    failure = None
    for task in done:
        try:
            await task  # Find the one with the exception
        except AssertionError as err:
            func = tasks[task]
            if failure is None or tasks[failure[0]]._step_num > func._step_num:
                failure = (task, err)

            if not func._optional_test:
                print('!!! One required test failed !!!\n')  # Extra new line
                print(f"    {func.__qualname__}() '{func.__doc__}'")
                print(*err.args)
                return 1
        except Exception:
            ...

    if failure is not None:
        func = tasks[failure[0]]
        # If it was a required test, we would have returned already
        print('??? One OPTIONAL test failed ???\n')  # Extra new line
        print(f"    {func.__qualname__}() '{func.__doc__}'")
        print(*failure[1].args)
        print(f'\nYou have already passed the qualifier, but failed at optional step {func._step_num}')

    return 0

def detect_test_files() -> list[ModuleType]:
    # An assumption is made here that, if the item ends with .py it is a file
    files = [f for f in os.listdir('tests') if f.startswith('test') and f.endswith('.py')]
    return [import_module('tests.' + mod[:-3]) for mod in files]


def discover_tests(mod: ModuleType) -> list[Callable[..., object]]:
    names = [symbol for symbol in dir(mod) if symbol.lower().startswith('test')]

    return [getattr(mod, name) for name in names]


def main() -> int:
    # Technically, [discover_tests(mod) for mod in detect_test_files()] becomes
    # a two-dimentional list which this flattens out to one list of functions.
    tests = [test for mod in detect_test_files() for test in discover_tests(mod)]
    return asyncio.run(run_tests(tests))

sys.exit(main())
