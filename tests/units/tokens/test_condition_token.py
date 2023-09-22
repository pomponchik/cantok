from functools import partial

import pytest

from cantok import SimpleToken, ConditionToken


def test_condition_counter():
    loop_size = 5
    def condition():
        for number in range(loop_size):
            yield False
        while True:
            yield True

    token = ConditionToken(partial(next, iter(condition())))

    counter = 0
    while not token.cancelled:
        counter += 1

    assert counter == loop_size


def test_condition_false():
    assert ConditionToken(lambda: False).cancelled == False
    assert ConditionToken(lambda: False).is_cancelled() == False
    assert ConditionToken(lambda: False).keep_on() == True


def test_condition_true():
    assert ConditionToken(lambda: True).cancelled == True
    assert ConditionToken(lambda: True).is_cancelled() == True
    assert ConditionToken(lambda: True).keep_on() == False


@pytest.mark.parametrize('arguments,expected_cancelled_status', [
    ([SimpleToken(), SimpleToken().cancel()], True),
    ([SimpleToken(), ConditionToken(lambda: True)], True),
    ([ConditionToken(lambda: False), ConditionToken(lambda: True)], True),
    ([SimpleToken()], False),
    ([ConditionToken(lambda: False)], False),
    ([SimpleToken().cancel()], True),
    ([ConditionToken(lambda: False).cancel()], True),
    ([ConditionToken(lambda: True).cancel()], True),
    ([SimpleToken(), SimpleToken()], False),
    ([SimpleToken(), SimpleToken(), SimpleToken()], False),
    ([SimpleToken(), SimpleToken(), SimpleToken(), SimpleToken()], False),
    ([ConditionToken(lambda: False), ConditionToken(lambda: False)], False),
    ([ConditionToken(lambda: False), ConditionToken(lambda: False), ConditionToken(lambda: False)], False),
])
def test_just_created_condition_token_with_arguments(arguments, expected_cancelled_status):
    assert ConditionToken(lambda: False, *arguments).cancelled == expected_cancelled_status
    assert ConditionToken(lambda: False, *arguments).is_cancelled() == expected_cancelled_status
    assert ConditionToken(lambda: False, *arguments).keep_on() == (not expected_cancelled_status)


def test_raise_without_first_argument():
    with pytest.raises(TypeError):
        ConditionToken()


def test_suppress_exception_false():
    def condition():
        raise ValueError

    token = ConditionToken(condition, suppress_exceptions=False)

    with pytest.raises(ValueError):
        token.cancelled


def test_suppress_exception_true():
    def condition():
        raise ValueError

    token = ConditionToken(condition, suppress_exceptions=True)

    assert token.cancelled == False


def test_suppress_exception_default_true():
    def condition():
        raise ValueError

    token = ConditionToken(condition)

    assert token.cancelled == False


def test_condition_function_returning_not_bool_value():
    assert ConditionToken(lambda: 'kek', suppress_exceptions=True).cancelled == False
    assert ConditionToken(lambda: 'kek').cancelled == False

    with pytest.raises(TypeError):
        ConditionToken(lambda: 'kek', suppress_exceptions=False).cancelled


@pytest.mark.parametrize(
    'suppress_exceptions_flag',
    [True, False],
)
@pytest.mark.parametrize(
    'default_flag',
    [True, False],
)
def test_test_representaion_of_extra_kwargs(suppress_exceptions_flag, default_flag):
    assert ConditionToken(
        lambda: False,
        suppress_exceptions=suppress_exceptions_flag,
        default=default_flag,
    ).text_representation_of_extra_kwargs() == f'suppress_exceptions={suppress_exceptions_flag}, default={default_flag}'


@pytest.mark.parametrize(
    'default',
    [True, False],
)
def test_default_if_exception(default):
    def condition():
        raise ValueError

    token = ConditionToken(condition, suppress_exceptions=True, default=default)

    assert token.cancelled == default


@pytest.mark.parametrize(
    'default',
    [True, False],
)
def test_default_if_not_bool(default):
    def condition():
        return 'kek'

    token = ConditionToken(condition, suppress_exceptions=True, default=default)

    assert token.cancelled == default
