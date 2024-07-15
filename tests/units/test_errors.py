import pytest

from cantok import AbstractToken, SimpleToken, ConditionToken, TimeoutToken, CounterToken, DefaultToken
from cantok import CancellationError, ConditionCancellationError, TimeoutCancellationError, CounterCancellationError, ImpossibleCancelError


def test_exception_inheritance_hierarchy():
    assert issubclass(ConditionCancellationError, CancellationError)
    assert issubclass(TimeoutCancellationError, CancellationError)
    assert issubclass(CounterCancellationError, CancellationError)
    assert issubclass(ImpossibleCancelError, CancellationError)


def test_exception_inheritance_hierarchy_from_view_of_tokens_classes():
    assert issubclass(ConditionToken.exception, SimpleToken.exception)
    assert issubclass(TimeoutToken.exception, SimpleToken.exception)
    assert issubclass(CounterToken.exception, SimpleToken.exception)
    assert issubclass(DefaultToken.exception, SimpleToken.exception)

    assert SimpleToken.exception is CancellationError
    assert ConditionToken.exception is ConditionCancellationError
    assert TimeoutToken.exception is TimeoutCancellationError
    assert CounterToken.exception is CounterCancellationError
    assert DefaultToken.exception is ImpossibleCancelError
