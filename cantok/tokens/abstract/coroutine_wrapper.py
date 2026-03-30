import sys
import weakref
from asyncio import sleep as async_sleep
from collections.abc import Coroutine
from time import sleep as sync_sleep
from types import TracebackType
from typing import Any, Dict, Optional, Union

from displayhooks import not_display


class WaitCoroutineWrapper(Coroutine):  # type: ignore[type-arg]
    def __init__(self, step: Union[int, float], token_for_wait: 'AbstractToken', token_for_check: 'AbstractToken') -> None:  # type: ignore[name-defined]
        self.step = step
        self.token_for_wait = token_for_wait
        self.token_for_check = token_for_check

        self.flags: Dict[str, bool] = {}
        self.coroutine = self.async_wait(step, self.flags, token_for_wait, token_for_check)

        weakref.finalize(self, self.sync_wait, step, self.flags, token_for_wait, token_for_check, self.coroutine)

    def __await__(self) -> Any:
        return self.coroutine.__await__()

    def send(self, value: Any) -> Any:
        return self.coroutine.send(value)

    def throw(self, exception_type: Any, value: Optional[Any] = None, traceback: Optional[TracebackType] = None) -> Any:
        pass  # pragma: no cover

    def close(self) -> None:
        pass  # pragma: no cover

    @staticmethod
    def sync_wait(step: Union[int, float], flags: Dict[str, bool], token_for_wait: 'AbstractToken', token_for_check: 'AbstractToken', wrapped_coroutine: Coroutine) -> None:  # type: ignore[type-arg, name-defined]
        if not flags.get('used', False):
            # In Python <=3.13, LOAD_FAST increments refcount, so getrefcount() returns
            # true_refs + 2; threshold < 5 means "fewer than 3 external refs" (i.e. only
            # the finalize args-tuple and this parameter hold the coroutine, indicating it
            # is not being actively awaited by the event loop).
            # In Python 3.14+, LOAD_FAST_BORROW does not increment refcount, AND
            # native_coro.__await__() returns a new coroutine_wrapper object instead of
            # the coroutine itself, so getrefcount() returns true_refs + 1; threshold < 4
            # expresses the same "fewer than 3 external refs" condition.
            _refcount_threshold = 4 if sys.version_info >= (3, 14) else 5
            if sys.getrefcount(wrapped_coroutine) < _refcount_threshold:
                wrapped_coroutine.close()

                while token_for_wait:
                    sync_sleep(step)

                token_for_check.check()

    @staticmethod
    async def async_wait(step: Union[int, float], flags: Dict[str, bool], token_for_wait: 'AbstractToken', token_for_check: 'AbstractToken') -> None:  # type: ignore[name-defined]
        flags['used'] = True

        while token_for_wait:  # noqa: ASYNC110
            await async_sleep(step)

        await async_sleep(0)

        token_for_check.check()


not_display(WaitCoroutineWrapper)
