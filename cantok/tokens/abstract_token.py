from enum import Enum
from abc import ABC, abstractmethod
from threading import RLock
from dataclasses import dataclass

from cantok.errors import CancellationError


class CancelCause(Enum):
    CANCELLED = 1
    SUPERPOWER = 2
    NOT_CANCELLED = 3

@dataclass
class CancellationReport:
    cause: CancelCause
    from_token: 'AbstractToken'


class AbstractToken(ABC):
    exception = CancellationError

    def __init__(self, *tokens: 'AbstractToken', cancelled=False):
        self.tokens = tokens
        self._cancelled = cancelled
        self.lock = RLock()

    def __repr__(self):
        other_tokens = ', '.join([repr(x) for x in self.tokens])
        if other_tokens:
            other_tokens += ', '
        superpower = self.text_representation_of_superpower()
        if superpower:
            superpower += ', '
        extra_kwargs = self.text_representation_of_extra_kwargs()
        if extra_kwargs:
            extra_kwargs = ', ' + extra_kwargs
        return f'{type(self).__name__}({superpower}{other_tokens}cancelled={self.cancelled}{extra_kwargs})'

    def __str__(self):
        cancelled_flag = 'cancelled' if self.cancelled else 'not cancelled'
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
    def cancelled(self, new_value) -> None:
        if new_value == True:
            self._cancelled = True
        else:
            if self._cancelled == True:
                raise ValueError('You cannot restore a cancelled token.')

    def keep_on(self) -> bool:
        return not self.is_cancelled()

    def is_cancelled(self) -> bool:
        return self.get_report().cause != CancelCause.NOT_CANCELLED

    def get_report(self) -> CancellationReport:
        if self._cancelled:
            return CancellationReport(
                cause=CancelCause.CANCELLED,
                from_token=self,
            )
        elif self.superpower():
            return CancellationReport(
                cause=CancelCause.SUPERPOWER,
                from_token=self,
            )

        for token in self.tokens:
            if token.is_cancelled_reflect():
                return token.get_report()

        return CancellationReport(
            cause=CancelCause.NOT_CANCELLED,
            from_token=self,
        )

    def is_cancelled_reflect(self):
        return self.is_cancelled()

    def cancel(self) -> 'AbstractToken':
        self._cancelled = True
        return self

    @abstractmethod
    def superpower(self) -> bool:  # pragma: no cover
        pass

    @abstractmethod
    def text_representation_of_superpower(self) -> str:  # pragma: no cover
        pass

    def text_representation_of_extra_kwargs(self) -> str:
        return ''

    def check(self) -> None:
        with self.lock:
            if self.is_cancelled_reflect():
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
