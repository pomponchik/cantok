from sys import getrefcount
from abc import ABC, abstractmethod
from threading import RLock
from typing import List, Dict, Awaitable, Optional, Union, Any

from cantok.errors import CancellationError
from cantok.tokens.abstract.cancel_cause import CancelCause
from cantok.tokens.abstract.report import CancellationReport
from cantok.tokens.abstract.coroutine_wrapper import WaitCoroutineWrapper
from cantok.types import IterableWithTokens


class AbstractToken(ABC):
    exception = CancellationError
    rollback_if_nondirect_polling = False

    def __init__(self, *tokens: 'AbstractToken', cancelled: bool = False) -> None:
        self.cached_report: Optional[CancellationReport] = None
        self._cancelled: bool = cancelled
        self.tokens: List[AbstractToken] = self.filter_tokens(tokens)

        self.lock: RLock = RLock()

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

        from cantok import SimpleToken, DefaultToken, TimeoutToken

        nested_tokens = []
        container_token: Optional[AbstractToken] = None

        if isinstance(self, TimeoutToken) and isinstance(item, TimeoutToken):
            if self.monotonic == item.monotonic and self.deadline >= item.deadline and getrefcount(self) < 4:
                item.tokens.extend(self.tokens)
                return item

        for token in self, item:
            if token._cancelled:
                return SimpleToken(cancelled=True)
            elif isinstance(token, SimpleToken) and getrefcount(token) < 6:
                nested_tokens.extend(token.tokens)
            elif isinstance(token, DefaultToken):
                pass
            elif not isinstance(token, SimpleToken) and getrefcount(token) < 6 and container_token is None:
                container_token = token
            else:
                nested_tokens.append(token)

        if container_token is None:
            return SimpleToken(*nested_tokens)
        else:
            container_token.tokens.extend(container_token.filter_tokens(nested_tokens))
            return container_token

    def __bool__(self) -> bool:
        return self.keep_on()

    def filter_tokens(self, tokens: IterableWithTokens) -> List['AbstractToken']:  # type: ignore[type-arg]
        from cantok import DefaultToken

        result: List[AbstractToken] = []

        for token in tokens:
            if isinstance(token, DefaultToken):
                pass
            else:
                result.append(token)

        return result

    @property
    def cancelled(self) -> bool:
        return self.is_cancelled()

    @cancelled.setter
    def cancelled(self, new_value: bool) -> None:
        with self.lock:
            if new_value == True:
                self._cancelled = True
            else:
                if self.is_cancelled():
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
        elif self.check_superpower(direct):
            return CancellationReport(
                cause=CancelCause.SUPERPOWER,
                from_token=self,
            )
        elif self.cached_report is not None:
            return self.cached_report

        for token in self.tokens:
            report = token.get_report(direct=False)
            if report.cause != CancelCause.NOT_CANCELLED:
                self.cached_report = report
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
