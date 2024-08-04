from typing import Any


class CancellationError(Exception):
    token: 'AbstractToken'  # type: ignore[name-defined]

    def __init__(self, message: str, token: 'AbstractToken') -> None:  # type: ignore[name-defined]
        self.token = token
        super().__init__(message)

class ConditionCancellationError(CancellationError):
    pass

class CounterCancellationError(CancellationError):
    pass

class TimeoutCancellationError(CancellationError):
    pass

class ImpossibleCancelError(CancellationError):
    pass
