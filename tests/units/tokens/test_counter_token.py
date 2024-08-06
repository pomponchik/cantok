from threading import Thread

import pytest

from cantok.tokens.abstract.abstract_token import CancelCause, CancellationReport
from cantok import CounterToken, SimpleToken, CounterCancellationError


@pytest.mark.parametrize(
    'iterations',
    [
        0,
        1,
        5,
        15,
    ],
)
def test_counter(iterations):
    token = CounterToken(iterations)
    counter = 0

    while not token.cancelled:
        counter += 1

    assert counter == iterations


def test_double_str():
    token = CounterToken(1)

    assert str(token) == str(token)


def test_counter_less_than_zero():
    with pytest.raises(ValueError):
        CounterToken(-1)


@pytest.mark.parametrize(
    'iterations',
    [
        10_000,
        50_000,
        1_000,
    ],
)
@pytest.mark.parametrize(
    'number_of_threads',
    [
        1,
        2,
        5,
    ],
)
def test_race_condition_for_counter(iterations, number_of_threads):
    results = []
    token = CounterToken(iterations)

    def decrementer(number):
        counter = 0
        while not token.cancelled:
            counter += 1
        results.append(counter)

    threads = [Thread(target=decrementer, args=(iterations / number_of_threads, )) for _ in range(number_of_threads)]

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()

    result = sum(results)
    assert result == iterations


@pytest.mark.parametrize(
    'kwargs,expected_result',
    [
        ({}, 5),
        ({'direct': True}, 5),
        ({'direct': False}, 4),
    ],
)
def test_direct_default_counter(kwargs, expected_result):
    nested_token = CounterToken(5, **kwargs)
    token = SimpleToken(nested_token)

    assert not token.cancelled
    assert nested_token.counter == expected_result

    assert not nested_token.cancelled
    assert nested_token.counter == expected_result - 1


def test_check_superpower_raised():
    token = CounterToken(5)

    while not token.cancelled:
        pass

    with pytest.raises(CounterCancellationError):
        token.check()

    try:
        token.check()
    except CounterCancellationError as e:
        assert str(e) == 'After 5 attempts, the counter was reset to zero.'
        assert e.token is token


def test_check_superpower_raised_nested():
    nested_token = CounterToken(5, direct=False)
    token = SimpleToken(nested_token)

    while not token.cancelled:
        pass

    with pytest.raises(CounterCancellationError):
        token.check()

    try:
        token.check()
    except CounterCancellationError as e:
        assert str(e) == 'After 5 attempts, the counter was reset to zero.'
        assert e.token is nested_token
        assert e.token.exception is type(e)


def test_get_report_cancelled():
    token = CounterToken(5)

    while not token.cancelled:
        pass

    report = token.get_report()

    assert isinstance(report, CancellationReport)
    assert report.cause == CancelCause.SUPERPOWER
    assert report.from_token is token


@pytest.mark.parametrize(
    'counter,counter_nested,from_token_is_nested',
    [
        (1, 0, True),
        (0, 1, False),
        (0, 0, False),
    ],
)
def test_get_report_cancelled_nested(counter, counter_nested, from_token_is_nested):
    nested_token = CounterToken(counter_nested)
    token = CounterToken(counter, nested_token)

    report = token.get_report()

    assert isinstance(report, CancellationReport)
    assert report.cause == CancelCause.SUPERPOWER
    if from_token_is_nested:
        assert report.from_token is nested_token
    else:
        assert report.from_token is token


@pytest.mark.parametrize(
    'function',
    [
        lambda token: token.check(),
        lambda token: token.is_cancelled(),
        lambda token: token.cancelled,
        lambda token: token.keep_on(),
    ],
)
@pytest.mark.parametrize(
    'initial_counter, final_counter',
    [
        (50, 49),
        (5, 4),
        (1, 0),
        (0, 0),
    ],
)
def test_check_is_decrementing_counter(function, initial_counter, final_counter):
    token = CounterToken(initial_counter)

    try:
        function(token)
    except CounterCancellationError:
        pass

    assert token.counter == final_counter


def test_check_is_decrementing_counter_when_nested_token_is_cancelled():
    nested_token = SimpleToken(cancelled=True)
    token = CounterToken(2, nested_token)

    try:
        token.check()
    except Exception as e:
        assert e.token is nested_token
        assert type(e) is nested_token.exception
        assert type(e) is not token.exception

    assert token.counter == 1

    try:
        token.check()
    except Exception as e:
        assert e.token is nested_token
        assert type(e) is nested_token.exception
        assert type(e) is not token.exception

    assert token.counter == 0

    try:
        token.check()
    except Exception as e:
        assert e.token is token
        assert type(e) is token.exception
        assert type(e) is not nested_token.exception


def test_decrement_counter_after_zero():
    token = CounterToken(0)

    token.is_cancelled()

    assert token.counter == 0


def test_quasitemp_counter_token_plus_temp_simple_token():
    token = CounterToken(0) + SimpleToken()

    assert isinstance(token, SimpleToken)
    assert len(token.tokens) == 1
    assert isinstance(token.tokens[0], CounterToken)


def test_not_quasitemp_counter_token_plus_temp_simple_token():
    counter_token = CounterToken(1)
    token = counter_token + SimpleToken()

    assert isinstance(token, SimpleToken)
    assert len(token.tokens) == 1
    assert isinstance(token.tokens[0], CounterToken)
    assert token.tokens[0] is counter_token


def test_quasitemp_counter_token_plus_not_temp_simple_token():
    simple_token = SimpleToken()
    token = CounterToken(1) + simple_token

    assert isinstance(token, SimpleToken)
    assert token is not simple_token
    assert len(token.tokens) == 2
    assert isinstance(token.tokens[0], CounterToken)
    assert token.tokens[1] is simple_token


def test_not_quasitemp_counter_token_plus_not_temp_simple_token():
    simple_token = SimpleToken()
    counter_token = CounterToken(1)
    token = counter_token + simple_token

    assert isinstance(token, SimpleToken)
    assert token is not simple_token
    assert len(token.tokens) == 2
    assert isinstance(token.tokens[0], CounterToken)
    assert token.tokens[0] is counter_token
    assert token.tokens[1] is simple_token


def test_quasitemp_counter_token_plus_temp_simple_token_reverse():
    token = SimpleToken() + CounterToken(1)

    assert isinstance(token, SimpleToken)
    assert len(token.tokens) == 1
    assert isinstance(token.tokens[0], CounterToken)


def test_not_quasitemp_counter_token_plus_temp_simple_token_reverse():
    counter_token = CounterToken(1)
    token = SimpleToken() + counter_token

    assert isinstance(token, SimpleToken)
    assert len(token.tokens) == 1
    assert isinstance(token.tokens[0], CounterToken)
    assert token.tokens[0] is counter_token


def test_quasitemp_counter_token_plus_not_temp_simple_token_reverse():
    simple_token = SimpleToken()
    token = simple_token + CounterToken(1)

    assert isinstance(token, SimpleToken)
    assert token is not simple_token
    assert len(token.tokens) == 2
    assert isinstance(token.tokens[1], CounterToken)
    assert token.tokens[0] is simple_token


def test_not_quasitemp_counter_token_plus_not_temp_simple_token_reverse():
    simple_token = SimpleToken()
    counter_token = CounterToken(1)
    token = simple_token + counter_token

    assert isinstance(token, SimpleToken)
    assert token is not simple_token
    assert len(token.tokens) == 2
    assert isinstance(token.tokens[1], CounterToken)
    assert token.tokens[1] is counter_token
    assert token.tokens[0] is simple_token


def test_zero_counter_token_report_is_about_superpower():
    for report in CounterToken(0).get_report(True), CounterToken(0).get_report(False):
        assert report.cause == CancelCause.SUPERPOWER


def test_repr_for_counter_token():
    assert repr(CounterToken(0)) == 'CounterToken(0)'
    assert repr(CounterToken(1)) == 'CounterToken(1)'
    assert repr(CounterToken(10000)) == 'CounterToken(10000)'

    assert repr(CounterToken(10000, CounterToken(10000))) == 'CounterToken(10000, CounterToken(10000))'
    assert repr(CounterToken(10000, CounterToken(10000), CounterToken(10000))) == 'CounterToken(10000, CounterToken(10000), CounterToken(10000))'

    assert repr(CounterToken(10000, direct=True)) == 'CounterToken(10000)'
    assert repr(CounterToken(10000, direct=False)) == 'CounterToken(10000, direct=False)'

    assert repr(CounterToken(10000, cancelled=False)) == 'CounterToken(10000)'
    assert repr(CounterToken(10000, cancelled=True)) == 'CounterToken(10000, cancelled=True)'

    assert repr(CounterToken(10000, direct=False, cancelled=True)) == 'CounterToken(10000, cancelled=True, direct=False)'
    assert repr(CounterToken(10000, CounterToken(10000), direct=False, cancelled=True)) == 'CounterToken(10000, CounterToken(10000), cancelled=True, direct=False)'
