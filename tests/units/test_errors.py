import pytest

from cantok import AbstractToken, SimpleToken, ConditionToken, TimeoutToken, CounterToken
from cantok import CancellationError, ConditionCancellationError, TimeoutCancellationError, CounterCancellationError


def test_exception_inheritance_hierarchy():
    assert issubclass(ConditionCancellationError, CancellationError)
    assert issubclass(TimeoutCancellationError, CancellationError)
    assert issubclass(CounterCancellationError, CancellationError)


def test_exception_inheritance_hierarchy_from_view_of_tokens_classes():
    assert issubclass(ConditionToken.exception, SimpleToken.exception)
    assert issubclass(TimeoutToken.exception, SimpleToken.exception)
    assert issubclass(CounterToken.exception, SimpleToken.exception)
