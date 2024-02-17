from cantok import CancellationError, ConditionCancellationError, TimeoutCancellationError, CounterCancellationError


def test_exception_inheritance_hierarchy():
    assert issubclass(ConditionCancellationError, CancellationError)
    assert issubclass(TimeoutCancellationError, CancellationError)
    assert issubclass(CounterCancellationError, CancellationError)

    assert issubclass(TimeoutCancellationError, ConditionCancellationError)
    assert issubclass(CounterCancellationError, ConditionCancellationError)
