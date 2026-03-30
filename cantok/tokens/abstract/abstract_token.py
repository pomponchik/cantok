import sys
from abc import ABC, abstractmethod
from sys import getrefcount
from threading import RLock
from typing import Any, Awaitable, Dict, List, Optional, Union

from cantok.errors import CancellationError
from cantok.tokens.abstract.cancel_cause import CancelCause
from cantok.tokens.abstract.coroutine_wrapper import WaitCoroutineWrapper
from cantok.tokens.abstract.report import CancellationReport
from cantok.types import IterableWithTokens

# In Python <=3.13, LOAD_FAST increments refcounts, so we can distinguish
# temporary tokens (0 external refs) from stored tokens (1+ external refs)
# by comparing getrefcount() against these thresholds.
# The TimeoutToken branch runs before the loop (no tuple/loop-var refs), so
# its threshold is lower (4) than the generic loop threshold.
# The generic loop threshold is 7 for Python 3.9+ (not 6 as in the original inline code)
# because calling is_temp(token) as a function adds 1 extra reference via parameter binding.
# Python 3.8 does not exhibit this extra reference, so its threshold stays at 6.
if sys.version_info < (3, 14):  # pragma: no cover
    _TIMEOUT_TOKEN_REFCOUNT_THRESHOLD = 4
    # Python 3.8 generates bytecode that results in one fewer reference when
    # is_temp(token) is called in the for-loop context vs Python 3.9+.
    # Python 3.9 changed function call mechanics (vectorcall improvements)
    # which adds one extra LOAD_FAST-incremented reference in this context.
    _GENERIC_TOKEN_REFCOUNT_THRESHOLD = 6 if sys.version_info < (3, 9) else 7


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
        elif report.from_token is self and report.cause == CancelCause.CANCELLED:
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

    def __add__(self, item: 'AbstractToken') -> 'AbstractToken':  # noqa: PLR0911
        if not isinstance(item, AbstractToken):
            raise TypeError('Cancellation Token can only be combined with another Cancellation Token.')

        from cantok import DefaultToken, SimpleToken, TimeoutToken  # noqa: PLC0415

        if self._cancelled or item._cancelled:
            return SimpleToken(cancelled=True)

        nested_tokens = []
        container_token: Optional[AbstractToken] = None

        if sys.version_info >= (3, 14):  # pragma: no cover
            # In Python 3.14+, LOAD_FAST_BORROW does not increment refcounts,
            # making refcount-based detection of temporary tokens unreliable.
            # Instead, inspect the caller's frame: a token is "temporary" if it
            # does not appear in the caller's local variables or module globals.
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
        else:  # pragma: no cover
            _self_is_temp = getrefcount(self) < _TIMEOUT_TOKEN_REFCOUNT_THRESHOLD
            _item_is_temp = getrefcount(item) < _TIMEOUT_TOKEN_REFCOUNT_THRESHOLD

            def is_temp(token: 'AbstractToken') -> bool:
                return getrefcount(token) < _GENERIC_TOKEN_REFCOUNT_THRESHOLD

        if isinstance(self, TimeoutToken) and isinstance(item, TimeoutToken) and self.monotonic == item.monotonic:
            if self.deadline >= item.deadline and _self_is_temp:
                if _item_is_temp:
                    item.tokens.extend(self.tokens)
                    return item
                if self.tokens:
                    return SimpleToken(*(self.tokens), item)
                return item
            if self.deadline < item.deadline and _item_is_temp:
                if _self_is_temp:
                    self.tokens.extend(item.tokens)
                    return self
                if item.tokens:
                    return SimpleToken(*(item.tokens), self)
                return self

        for token in self, item:
            if isinstance(token, SimpleToken) and is_temp(token):
                nested_tokens.extend(token.tokens)
            elif isinstance(token, DefaultToken):
                pass
            elif not isinstance(token, SimpleToken) and is_temp(token) and container_token is None:
                container_token = token
            else:
                nested_tokens.append(token)

        if container_token is None:
            return SimpleToken(*nested_tokens)
        container_token.tokens.extend(container_token.filter_tokens(nested_tokens))
        return container_token

    def __bool__(self) -> bool:
        return self.keep_on()

    def filter_tokens(self, tokens: IterableWithTokens) -> List['AbstractToken']:
        from cantok import DefaultToken  # noqa: PLC0415

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
            elif self.is_cancelled():
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
            from cantok import SimpleToken  # noqa: PLC0415
            token: AbstractToken = SimpleToken()
        else:
            from cantok import TimeoutToken  # noqa: PLC0415
            token = TimeoutToken(timeout)

        return WaitCoroutineWrapper(step, self + token, token)

    def get_report(self, direct: bool = True) -> CancellationReport:
        if self._cancelled:
            return CancellationReport(
                cause=CancelCause.CANCELLED,
                from_token=self,
            )
        if self.check_superpower(direct):
            return CancellationReport(
                cause=CancelCause.SUPERPOWER,
                from_token=self,
            )
        if self.cached_report is not None:
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

    def superpower_rollback(self, superpower_data: Dict[str, Any]) -> None:  # pragma: no cover  # noqa: B027
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
        pairs: List[str] = [f'{key}={value!r}' for key, value in kwargs.items()]
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
