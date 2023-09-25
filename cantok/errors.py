class AbstractCancellationError(Exception):
    pass

class CancellationError(AbstractCancellationError):
    pass

class ConditionCancellationError(AbstractCancellationError):
    pass

class CounterCancellationError(AbstractCancellationError):
    pass

class TimeoutCancellationError(AbstractCancellationError):
    pass
