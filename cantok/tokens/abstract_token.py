import weakref
from sys import getrefcount
from enum import Enum
from time import sleep as sync_sleep
from asyncio import sleep as async_sleep
from abc import ABC, abstractmethod
from threading import RLock
from dataclasses import dataclass
from typing import List, Dict, Awaitable, Optional, Union, Any
from types import TracebackType
from collections.abc import Coroutine

from cantok.errors import CancellationError


class CancelCause(Enum):
    CANCELLED = 1
    SUPERPOWER = 2
    NOT_CANCELLED = 3

class WaitCoroutineWrapper(Coroutine):  # type: ignore[type-arg]
    def __init__(self, step: Union[int, float], token_for_wait: 'AbstractToken', token_for_check: 'AbstractToken') -> None:
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
    def sync_wait(step: Union[int, float], flags: Dict[str, bool], token_for_wait: 'AbstractToken', token_for_check: 'AbstractToken', wrapped_coroutine: Coroutine) -> None:  # type: ignore[type-arg]
        if not flags.get('used', False):
            if getrefcount(wrapped_coroutine) < 5:
                wrapped_coroutine.close()

                while token_for_wait:
                    sync_sleep(step)

                token_for_check.check()

    @staticmethod
    async def async_wait(step: Union[int, float], flags: Dict[str, bool], token_for_wait: 'AbstractToken', token_for_check: 'AbstractToken') -> None:
        flags['used'] = True

        while token_for_wait:
            await async_sleep(step)

        await async_sleep(0)

        token_for_check.check()

@dataclass
class CancellationReport:
    cause: CancelCause
    from_token: 'AbstractToken'

class AbstractToken(ABC):
    exception = CancellationError
    rollback_if_nondirect_polling = False

    def __init__(self, *tokens: 'AbstractToken', cancelled: bool = False) -> None:
        self.tokens = tokens
        self._cancelled = cancelled
        self.lock = RLock()

    def __repr__(self) -> str:
        chunks = []
        superpower = self.text_representation_of_superpower()
        if superpower:
            chunks.append(superpower)
        other_tokens = ', '.join([repr(x) for x in self.tokens])
        if other_tokens:
            chunks.append(other_tokens)
        report = self.get_report(direct=False)
        if report.cause == CancelCause.NOT_CANCELLED:
            extra_kwargs = {}
        else:
            if report.from_token is self and report.cause == CancelCause.CANCELLED:
                extra_kwargs = {'cancelled': True}
            else:
                extra_kwargs = {}
        extra_kwargs.update(**(self.get_extra_kwargs()))
        text_representation_of_extra_kwargs = self.text_representation_of_kwargs(**extra_kwargs)
        if text_representation_of_extra_kwargs:
            chunks.append(text_representation_of_extra_kwargs)

        glued_chunks = ', '.join(chunks)
        return f'{type(self).__name__}({glued_chunks})'

    def __str__(self) -> str:
        cancelled_flag = 'cancelled' if self.is_cancelled(direct=False) else 'not cancelled'
        return f'<{type(self).__name__} ({cancelled_flag})>'

    def __add__(self, item: 'AbstractToken') -> 'AbstractToken':
        if not isinstance(item, AbstractToken):
            raise TypeError('Cancellation Token can only be combined with another Cancellation Token.')

        from cantok import SimpleToken

        return SimpleToken(self, item)

    def __bool__(self) -> bool:
        return self.keep_on()

    @property
    def cancelled(self) -> bool:
        return self.is_cancelled()

    @cancelled.setter
    def cancelled(self, new_value: bool) -> None:
        if new_value == True:
            self._cancelled = True
        else:
            if self._cancelled == True:
                raise ValueError('You cannot restore a cancelled token.')

    def keep_on(self) -> bool:
        return not self.is_cancelled()

    def is_cancelled(self, direct: bool = True) -> bool:
        return self.get_report(direct=direct).cause != CancelCause.NOT_CANCELLED

    def wait(self, step: Union[int, float] = 0.0001, timeout: Optional[Union[int, float]] = None) -> Awaitable:  # type: ignore[type-arg]
        if step < 0:
            raise ValueError('The token polling iteration time cannot be less than zero.')
        if timeout is not None and timeout < 0:
            raise ValueError('The total timeout of waiting cannot be less than zero.')
        if timeout is not None and step > timeout:
            raise ValueError('The total timeout of waiting cannot be less than the time of one iteration of the token polling.')

        if timeout is None:
            from cantok import SimpleToken
            token: AbstractToken = SimpleToken()
        else:
            from cantok import TimeoutToken
            token = TimeoutToken(timeout)

        return WaitCoroutineWrapper(step, self + token, token)

    def get_report(self, direct: bool = True) -> CancellationReport:
        if self._cancelled:
            return CancellationReport(
                cause=CancelCause.CANCELLED,
                from_token=self,
            )
        else:
            if self.check_superpower(direct):
                return CancellationReport(
                    cause=CancelCause.SUPERPOWER,
                    from_token=self,
                )

        for token in self.tokens:
            report = token.get_report(direct=False)
            if report.cause != CancelCause.NOT_CANCELLED:
                return report

        return CancellationReport(
            cause=CancelCause.NOT_CANCELLED,
            from_token=self,
        )

    def cancel(self) -> 'AbstractToken':
        self._cancelled = True
        return self

    @abstractmethod
    def superpower(self) -> bool:  # pragma: no cover
        pass

    def superpower_rollback(self, superpower_data: Dict[str, Any]) -> None:  # pragma: no cover
        pass

    def check_superpower(self, direct: bool) -> bool:
        if self.rollback_if_nondirect_polling and not direct:
            return self.check_superpower_with_rollback()
        return self.superpower()

    def check_superpower_with_rollback(self) -> bool:
        with self.lock:
            superpower_data = self.get_superpower_data()
            result = self.superpower()
            self.superpower_rollback(superpower_data)
            return result

    def get_superpower_data(self) -> Dict[str, Any]:  # pragma: no cover
        return {}

    @abstractmethod
    def text_representation_of_superpower(self) -> str:  # pragma: no cover
        pass

    def get_extra_kwargs(self) -> Dict[str, Any]:
        return {}

    def text_representation_of_extra_kwargs(self) -> str:
        return self.text_representation_of_kwargs(**(self.get_extra_kwargs()))

    def text_representation_of_kwargs(self, **kwargs: Any) -> str:
        pairs: List[str] = [f'{key}={repr(value)}' for key, value in kwargs.items()]
        return ', '.join(pairs)

    def check(self) -> None:
        with self.lock:
            report = self.get_report()

            if report.cause == CancelCause.CANCELLED:
                report.from_token.raise_cancelled_exception()

            elif report.cause == CancelCause.SUPERPOWER:
                report.from_token.raise_superpower_exception()

    def raise_cancelled_exception(self) -> None:
        raise CancellationError('The token has been cancelled.', self)

    def raise_superpower_exception(self) -> None:
        raise self.exception(self.get_superpower_exception_message(), self)

    @abstractmethod
    def get_superpower_exception_message(self) -> str:  # pragma: no cover
        return 'You have done the impossible to see this error.'
