from typing import Any

class CancellationError(Exception):
    def __init__(self, message: str, token: Any):
        self.token = token
        super().__init__(message)

class ConditionCancellationError(CancellationError):
    pass

class CounterCancellationError(CancellationError):
    pass

class TimeoutCancellationError(CancellationError):
    pass
