import sys
from abc import ABC, abstractmethod
from threading import RLock
from typing import Any, Awaitable, Dict, List, Optional, Union

from cantok.errors import CancellationError
from cantok.tokens.abstract.cancel_cause import CancelCause
from cantok.tokens.abstract.coroutine_wrapper import WaitCoroutineWrapper
from cantok.tokens.abstract.report import CancellationReport
from cantok.types import IterableWithTokens


class AbstractToken(ABC):
    exception = CancellationError
    _rollback_if_nondirect_polling = False

    def __init__(self, *tokens: 'AbstractToken', cancelled: bool = False) -> None:
        self._cached_report: Optional[CancellationReport] = None
        self._cancelled: bool = cancelled
        self._tokens: List[AbstractToken] = self._filter_tokens(tokens)

        self._lock: RLock = RLock()

    def __repr__(self) -> str:
        chunks = []
        superpower = self._text_representation_of_superpower()
        if superpower:
            chunks.append(superpower)
        other_tokens = ', '.join([repr(x) for x in self._tokens])
        if other_tokens:
            chunks.append(other_tokens)
        report = self._get_report(direct=False)
        if report.cause == CancelCause.NOT_CANCELLED:
            extra_kwargs = {}
        elif report.from_token is self and report.cause == CancelCause.CANCELLED:
            extra_kwargs = {'cancelled': True}
        else:
            extra_kwargs = {}
        extra_kwargs.update(**(self._get_extra_kwargs()))
        text_representation_of_extra_kwargs = self._text_representation_of_kwargs(**extra_kwargs)
        if text_representation_of_extra_kwargs:
            chunks.append(text_representation_of_extra_kwargs)

        glued_chunks = ', '.join(chunks)
        return f'{type(self).__name__}({glued_chunks})'

    def __str__(self) -> str:
        cancelled_flag = 'cancelled' if self.is_cancelled(direct=False) else 'not cancelled'
        return f'<{type(self).__name__} ({cancelled_flag})>'

    def __add__(self, item: 'AbstractToken') -> 'AbstractToken':  # noqa: PLR0911
        if not isinstance(item, AbstractToken):
            raise TypeError('Cancellation Token can only be combined with another Cancellation Token.')

        from cantok import DefaultToken, SimpleToken, TimeoutToken  # noqa: PLC0415

        if self._cancelled or item._cancelled:
            return SimpleToken(cancelled=True)

        nested_tokens = []
        container_token: Optional[AbstractToken] = None

        # Inspect the caller's frame to determine if a token is "temporary"
        # (not stored in any variable). This is robust across all Python versions,
        # unlike refcount-based detection which varies with bytecode optimizations.
        _frame = sys._getframe(1)
        _caller_locals = list(_frame.f_locals.values())
        _caller_globals = list(_frame.f_globals.values())

        def is_temp(token: 'AbstractToken') -> bool:
            for v in _caller_locals:
                if v is token:
                    return False
            return all(v is not token for v in _caller_globals)

        _self_is_temp = is_temp(self)
        _item_is_temp = is_temp(item)

        if isinstance(self, TimeoutToken) and isinstance(item, TimeoutToken) and self._monotonic == item._monotonic:
            if self._deadline >= item._deadline and _self_is_temp:
                if _item_is_temp:
                    item._tokens.extend(self._tokens)
                    return item
                if self._tokens:
                    return SimpleToken(*(self._tokens), item)
                return item
            if self._deadline < item._deadline and _item_is_temp:
                if _self_is_temp:
                    self._tokens.extend(item._tokens)
                    return self
                if item._tokens:
                    return SimpleToken(*(item._tokens), self)
                return self

        for token in self, item:
            if isinstance(token, SimpleToken) and is_temp(token):
                nested_tokens.extend(token._tokens)
            elif isinstance(token, DefaultToken):
                pass
            elif not isinstance(token, SimpleToken) and is_temp(token) and container_token is None:
                container_token = token
            else:
                nested_tokens.append(token)

        if container_token is None:
            return SimpleToken(*nested_tokens)
        container_token._tokens.extend(container_token._filter_tokens(nested_tokens))
        return container_token

    def __bool__(self) -> bool:
        return self.keep_on()

    @property
    def cancelled(self) -> bool:
        return self.is_cancelled()

    @cancelled.setter
    def cancelled(self, new_value: bool) -> None:
        with self._lock:
            if new_value == True:
                self._cancelled = True
            elif self.is_cancelled():
                raise ValueError('You cannot restore a cancelled token.')

    def keep_on(self) -> bool:
        return not self.is_cancelled()

    def is_cancelled(self, direct: bool = True) -> bool:
        return self._get_report(direct=direct).cause != CancelCause.NOT_CANCELLED

    def wait(self, step: Union[int, float] = 0.0001, timeout: Optional[Union[int, float]] = None) -> Awaitable:  # type: ignore[type-arg]
        if step < 0:
            raise ValueError('The token polling iteration time cannot be less than zero.')
        if timeout is not None and timeout < 0:
            raise ValueError('The total timeout of waiting cannot be less than zero.')
        if timeout is not None and step > timeout:
            raise ValueError('The total timeout of waiting cannot be less than the time of one iteration of the token polling.')

        if timeout is None:
            from cantok import SimpleToken  # noqa: PLC0415
            token: AbstractToken = SimpleToken()
        else:
            from cantok import TimeoutToken  # noqa: PLC0415
            token = TimeoutToken(timeout)

        return WaitCoroutineWrapper(step, self + token, token)

    def cancel(self) -> 'AbstractToken':
        self._cancelled = True
        return self

    def check(self) -> None:
        with self._lock:
            report = self._get_report()

            if report.cause == CancelCause.CANCELLED:
                report.from_token._raise_cancelled_exception()

            elif report.cause == CancelCause.SUPERPOWER:
                report.from_token._raise_superpower_exception()

    def _filter_tokens(self, tokens: IterableWithTokens) -> List['AbstractToken']:
        from cantok import DefaultToken  # noqa: PLC0415

        result: List[AbstractToken] = []

        for token in tokens:
            if isinstance(token, DefaultToken):
                pass
            else:
                result.append(token)

        return result

    def _get_report(self, direct: bool = True) -> CancellationReport:
        if self._cancelled:
            return CancellationReport(
                cause=CancelCause.CANCELLED,
                from_token=self,
            )
        if self._check_superpower(direct):
            return CancellationReport(
                cause=CancelCause.SUPERPOWER,
                from_token=self,
            )
        if self._cached_report is not None:
            return self._cached_report

        for token in self._tokens:
            report = token._get_report(direct=False)
            if report.cause != CancelCause.NOT_CANCELLED:
                self._cached_report = report
                return report

        return CancellationReport(
            cause=CancelCause.NOT_CANCELLED,
            from_token=self,
        )

    @abstractmethod
    def _superpower(self) -> bool:  # pragma: no cover
        pass

    def _superpower_rollback(self, superpower_data: Dict[str, Any]) -> None:  # pragma: no cover  # noqa: B027
        pass

    def _check_superpower(self, direct: bool) -> bool:
        if self._rollback_if_nondirect_polling and not direct:
            return self._check_superpower_with_rollback()
        return self._superpower()

    def _check_superpower_with_rollback(self) -> bool:
        with self._lock:
            superpower_data = self._get_superpower_data()
            result = self._superpower()
            self._superpower_rollback(superpower_data)
            return result

    def _get_superpower_data(self) -> Dict[str, Any]:  # pragma: no cover
        return {}

    @abstractmethod
    def _text_representation_of_superpower(self) -> str:  # pragma: no cover
        pass

    def _get_extra_kwargs(self) -> Dict[str, Any]:
        return {}

    def _text_representation_of_extra_kwargs(self) -> str:
        return self._text_representation_of_kwargs(**(self._get_extra_kwargs()))

    def _text_representation_of_kwargs(self, **kwargs: Any) -> str:
        pairs: List[str] = [f'{key}={value!r}' for key, value in kwargs.items()]
        return ', '.join(pairs)

    def _raise_cancelled_exception(self) -> None:
        raise CancellationError('The token has been cancelled.', self)

    def _raise_superpower_exception(self) -> None:
        raise self.exception(self._get_superpower_exception_message(), self)

    @abstractmethod
    def _get_superpower_exception_message(self) -> str:  # pragma: no cover
        return 'You have done the impossible to see this error.'
