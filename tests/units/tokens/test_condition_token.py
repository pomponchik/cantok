import asyncio
from time import perf_counter
from functools import partial

import pytest

from cantok.tokens.abstract.abstract_token import CancelCause, CancellationReport
from cantok import SimpleToken, ConditionToken, ConditionCancellationError


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


def test_check_superpower_raised():
    token = ConditionToken(lambda: True)

    with pytest.raises(ConditionCancellationError):
        token.check()

    try:
        token.check()
    except ConditionCancellationError as e:
        assert str(e) == 'The cancellation condition was satisfied.'
        assert e.token is token


def test_check_superpower_raised_nested():
    nested_token = ConditionToken(lambda: True)
    token = SimpleToken(nested_token)

    with pytest.raises(ConditionCancellationError):
        token.check()

    try:
        token.check()
    except ConditionCancellationError as e:
        assert str(e) == 'The cancellation condition was satisfied.'
        assert e.token is nested_token
        assert e.token.exception is type(e)


def test_get_report_cancelled():
    token = ConditionToken(lambda: True)

    report = token.get_report()

    assert isinstance(report, CancellationReport)
    assert report.cause == CancelCause.SUPERPOWER
    assert report.from_token is token


@pytest.mark.parametrize(
    'cancelled,cancelled_nested,from_token_is_nested',
    [
        (True, False, False),
        (False, True, True),
        (True, True, False),
    ],
)
def test_get_report_cancelled_nested(cancelled, cancelled_nested, from_token_is_nested):
    nested_token = ConditionToken(lambda: cancelled_nested)
    token = ConditionToken(lambda: cancelled, nested_token)

    report = token.get_report()

    assert isinstance(report, CancellationReport)
    assert report.cause == CancelCause.SUPERPOWER
    if from_token_is_nested:
        assert report.from_token is nested_token
    else:
        assert report.from_token is token


def test_async_wait_condition():
    flag = False
    timeout = 0.001
    token = ConditionToken(lambda: flag)

    async def cancel_with_timeout(token):
        nonlocal flag
        await asyncio.sleep(timeout)
        flag = True

    async def runner():
        return await asyncio.gather(token.wait(), cancel_with_timeout(token))

    start_time = perf_counter()
    asyncio.run(runner())
    finish_time = perf_counter()

    assert finish_time - start_time >= timeout



@pytest.mark.parametrize(
    'options',
    [
        {},
        {'suppress_exceptions': True},
        {'suppress_exceptions': False},
    ],
)
def test_order_of_callbacks(options):
    lst = []
    token = ConditionToken(lambda: lst.append(2) is not None, before=lambda: lst.append(1), after=lambda: lst.append(3), **options)

    token.check()

    assert lst == [1, 2, 3]


@pytest.mark.parametrize(
    'options',
    [
        {},
        {'suppress_exceptions': True},
    ],
)
def test_raise_suppressed_exception_in_before_callback(options):
    lst = []

    def before_callback():
        lst.append(1)
        raise ValueError

    token = ConditionToken(lambda: lst.append(2) is not None, before=before_callback, after=lambda: lst.append(3), **options)

    token.check()

    assert lst == [1, 2, 3]


@pytest.mark.parametrize(
    'options',
    [
        {},
        {'suppress_exceptions': True},
    ],
)
def test_raise_suppressed_exception_in_after_callback(options):
    lst = []

    def after_callback():
        lst.append(3)
        raise ValueError

    token = ConditionToken(lambda: lst.append(2) is not None, before=lambda: lst.append(1), after=after_callback, **options)

    token.check()

    assert lst == [1, 2, 3]


def test_raise_not_suppressed_exception_in_before_callback():
    lst = []

    token = ConditionToken(lambda: lst.append(2) is not None, before=lambda: 1 / 0, suppress_exceptions=False)

    with pytest.raises(ZeroDivisionError):
        token.check()

    assert not lst


def test_raise_not_suppressed_exception_in_after_callback():
    lst = []

    token = ConditionToken(lambda: lst.append(2) is not None, before=lambda: lst.append(1), after=lambda: 1 / 0, suppress_exceptions=False)

    with pytest.raises(ZeroDivisionError):
        token.check()

    assert lst == [1, 2]


@pytest.mark.parametrize(
    'options',
    [
        {},
        {'caching': True},
        {'caching': False},
    ],
)
def test_cached_condition_cancelling(options):
    counter = 0

    def condition():
        nonlocal counter
        counter +=1
        return counter == 3

    token = ConditionToken(condition, **options)

    token.wait()

    if options.get('caching', True):
        assert counter == 3
        assert token.cancelled == True
        assert counter == 3
        with pytest.raises(ConditionCancellationError):
            token.check()
        assert counter == 3
        assert token.cancelled == True
        assert counter == 3
    else:
        assert counter == 3
        assert token.cancelled == False
        assert counter == 4
        token.check()
        assert counter == 5
        assert token.cancelled == False
        assert counter == 6


def test_quasitemp_condition_token_plus_temp_simple_token():
    token = ConditionToken(lambda: False) + SimpleToken()

    assert isinstance(token, SimpleToken)
    assert len(token.tokens) == 1
    assert isinstance(token.tokens[0], ConditionToken)


def test_not_quasitemp_condition_token_plus_temp_simple_token():
    condition_token = ConditionToken(lambda: False)
    token = condition_token + SimpleToken()

    assert isinstance(token, SimpleToken)
    assert len(token.tokens) == 1
    assert isinstance(token.tokens[0], ConditionToken)
    assert token.tokens[0] is condition_token


def test_quasitemp_condition_token_plus_not_temp_simple_token():
    simple_token = SimpleToken()
    token = ConditionToken(lambda: False) + simple_token

    assert isinstance(token, SimpleToken)
    assert token is not simple_token
    assert len(token.tokens) == 2
    assert isinstance(token.tokens[0], ConditionToken)
    assert token.tokens[1] is simple_token


def test_not_quasitemp_condition_token_plus_not_temp_simple_token():
    simple_token = SimpleToken()
    condition_token = ConditionToken(lambda: False)
    token = condition_token + simple_token

    assert isinstance(token, SimpleToken)
    assert token is not simple_token
    assert len(token.tokens) == 2
    assert isinstance(token.tokens[0], ConditionToken)
    assert token.tokens[0] is condition_token
    assert token.tokens[1] is simple_token


def test_quasitemp_condition_token_plus_temp_simple_token_reverse():
    token = SimpleToken() + ConditionToken(lambda: False)

    assert isinstance(token, SimpleToken)
    assert len(token.tokens) == 1
    assert isinstance(token.tokens[0], ConditionToken)


def test_not_quasitemp_condition_token_plus_temp_simple_token_reverse():
    condition_token = ConditionToken(lambda: False)
    token = SimpleToken() + condition_token

    assert isinstance(token, SimpleToken)
    assert len(token.tokens) == 1
    assert isinstance(token.tokens[0], ConditionToken)
    assert token.tokens[0] is condition_token


def test_quasitemp_condition_token_plus_not_temp_simple_token_reverse():
    simple_token = SimpleToken()
    token = simple_token + ConditionToken(lambda: False)

    assert isinstance(token, SimpleToken)
    assert token is not simple_token
    assert len(token.tokens) == 2
    assert isinstance(token.tokens[1], ConditionToken)
    assert token.tokens[0] is simple_token


def test_not_quasitemp_condition_token_plus_not_temp_simple_token_reverse():
    simple_token = SimpleToken()
    condition_token = ConditionToken(lambda: False)
    token = simple_token + condition_token

    assert isinstance(token, SimpleToken)
    assert token is not simple_token
    assert len(token.tokens) == 2
    assert isinstance(token.tokens[1], ConditionToken)
    assert token.tokens[1] is condition_token
    assert token.tokens[0] is simple_token
