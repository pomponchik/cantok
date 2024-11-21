from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from cantok.tokens.abstract.abstract_token import AbstractToken


class CancellationError(Exception):
    """Base class for cancellation exceptions in this module."""
    token: AbstractToken

    def __init__(self, message: str, token: AbstractToken) -> None:
        self.token = token
        super().__init__(message)


class ConditionCancellationError(CancellationError):
    """If token is cancelled by condition."""
    pass

class CounterCancellationError(ConditionCancellationError):
    """If token is cancelled by counter.

    CounterToken derives from ConditionToken.
    """
    pass


class TimeoutCancellationError(ConditionCancellationError, TimeoutError):
    """If token is cancelled by timeout.

    TimeoutToken derives from ConditionToken.
    """
    pass


class ImpossibleCancelError(CancellationError):
    """Token cancellation is impossible."""
    pass
