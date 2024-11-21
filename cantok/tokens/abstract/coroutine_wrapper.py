import sys
import weakref
from typing import Dict, Union, Optional, Any
from types import TracebackType
from collections.abc import Coroutine
from time import sleep as sync_sleep
from asyncio import sleep as async_sleep

from displayhooks import not_display


class WaitCoroutineWrapper(Coroutine):
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
            if sys.getrefcount(wrapped_coroutine) < 5:
                wrapped_coroutine.close()

                while token_for_wait:
                    sync_sleep(step)

                token_for_check.check()

    @staticmethod
    async def async_wait(step: Union[int, float], flags: Dict[str, bool], token_for_wait: 'AbstractToken', token_for_check: 'AbstractToken') -> None:  # type: ignore[name-defined]
        flags['used'] = True

        while token_for_wait:
            await async_sleep(step)

        await async_sleep(0)

        token_for_check.check()


not_display(WaitCoroutineWrapper)
