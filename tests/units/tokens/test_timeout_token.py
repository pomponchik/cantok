import asyncio
from time import sleep, perf_counter

import pytest

from cantok.tokens.abstract.abstract_token import CancelCause, CancellationReport
from cantok import SimpleToken, TimeoutToken, TimeoutCancellationError


@pytest.mark.parametrize(
    'options',
    [
        {},
        {'monotonic': True},
        {'monotonic': False},
    ],
)
@pytest.mark.parametrize(
    'zero_timeout',
    [
        0,
        0.0,
    ],
)
def test_zero_timeout(zero_timeout, options):
    token = TimeoutToken(zero_timeout, **options)

    assert token.cancelled == True
    assert token.cancelled == True
    assert token.is_cancelled() == True
    assert token.is_cancelled() == True
    assert token.keep_on() == False
    assert token.keep_on() == False


@pytest.mark.parametrize(
    'options',
    [
        {},
        {'monotonic': True},
        {'monotonic': False},
    ],
)
@pytest.mark.parametrize(
    'timeout',
    [
        -1,
        -0.5,
    ],
)
def test_less_than_zero_timeout(options, timeout):
    with pytest.raises(ValueError, match='You cannot specify a timeout less than zero.'):
        TimeoutToken(timeout, **options)


def test_raise_without_first_argument():
    with pytest.raises(TypeError):
        TimeoutToken()


@pytest.mark.parametrize(
    'options',
    [
        {},
        {'monotonic': True},
        {'monotonic': False},
    ],
)
def test_timeout_expired(options):
    timeout = 0.1
    token = TimeoutToken(timeout, **options)

    assert token.cancelled == False
    assert token.cancelled == False
    assert token.is_cancelled() == False
    assert token.is_cancelled() == False
    assert token.keep_on() == True
    assert token.keep_on() == True

    sleep(timeout * 2)

    assert token.cancelled == True
    assert token.cancelled == True
    assert token.is_cancelled() == True
    assert token.is_cancelled() == True
    assert token.keep_on() == False
    assert token.keep_on() == False


def test_text_representaion_of_extra_kwargs():
    assert TimeoutToken(5, monotonic=False).text_representation_of_extra_kwargs() == ''
    assert TimeoutToken(5, monotonic=True).text_representation_of_extra_kwargs() == 'monotonic=True'
    assert TimeoutToken(5).text_representation_of_extra_kwargs() == ''


@pytest.mark.parametrize(
    ['options', 'repr_string'],
    [
        ({}, 'TimeoutToken(1)'),
        ({'monotonic': True}, 'TimeoutToken(1, monotonic=True)'),
        ({'monotonic': False}, 'TimeoutToken(1)'),
    ],
)
def test_repr_of_timeout_token(options, repr_string):
    assert repr(TimeoutToken(1, **options)) == repr_string


def test_check_superpower_raised():
    token = TimeoutToken(0.125)

    while not token.cancelled:
        pass

    with pytest.raises(TimeoutCancellationError):
        token.check()

    try:
        token.check()
    except TimeoutCancellationError as e:
        assert str(e) == 'The timeout of 0.125 seconds has expired.'
        assert e.token is token


@pytest.mark.parametrize(
    'timeout',
    [
        0.125,
        0,
    ],
)
def test_check_superpower_raised_nested(timeout):
    nested_token = TimeoutToken(timeout)
    token = SimpleToken(nested_token)

    while not token.cancelled:
        pass

    with pytest.raises(TimeoutCancellationError):
        token.check()

    try:
        token.check()
    except TimeoutCancellationError as e:
        assert str(e) == f'The timeout of {timeout} seconds has expired.'
        assert e.token is nested_token
        assert e.token.exception is type(e)


def test_get_report_cancelled():
    token = TimeoutToken(0)

    while not token.cancelled:
        pass

    report = token.get_report()

    assert isinstance(report, CancellationReport)
    assert report.cause == CancelCause.SUPERPOWER
    assert report.from_token is token


@pytest.mark.parametrize(
    'timeout,timeout_nested,from_token_is_nested',
    [
        (0, 0, False),
        (1, 0, True),
        (0, 1, False),
    ],
)
def test_get_report_cancelled_nested(timeout, timeout_nested, from_token_is_nested):
    nested_token = TimeoutToken(timeout_nested)
    token = TimeoutToken(timeout, nested_token)

    report = token.get_report()

    assert isinstance(report, CancellationReport)
    assert report.cause == CancelCause.SUPERPOWER
    if from_token_is_nested:
        assert report.from_token is nested_token
    else:
        assert report.from_token is token


def test_async_wait_timeout():
    sleep_duration = 0.0001
    token = TimeoutToken(sleep_duration)

    start_time = perf_counter()
    asyncio.run(token.wait())
    finish_time = perf_counter()

    assert sleep_duration <= finish_time - start_time


def test_run_async_multiple_timeouts():
    sleep_duration = 0.001
    number_of_tokens = 100

    tokens = [TimeoutToken(sleep_duration) for x in range(number_of_tokens)]

    async def runner():
        return await asyncio.gather(*(x.wait() for x in tokens))

    start_time = perf_counter()
    asyncio.run(runner())
    finish_time = perf_counter()

    print(finish_time - start_time)

    assert (finish_time - start_time) < (sleep_duration * number_of_tokens)


def test_timeout_wait():
    sleep_duration = 1
    token = TimeoutToken(sleep_duration)

    start_time = perf_counter()
    token.wait()
    finish_time = perf_counter()

    assert sleep_duration <= finish_time - start_time


def test_quasitemp_timeout_token_plus_temp_simple_token():
    token = TimeoutToken(1) + SimpleToken()

    assert isinstance(token, SimpleToken)
    assert len(token.tokens) == 1
    assert isinstance(token.tokens[0], TimeoutToken)


def test_not_quasitemp_timeout_token_plus_temp_simple_token():
    timeout_token = TimeoutToken(1)
    token = timeout_token + SimpleToken()

    assert isinstance(token, SimpleToken)
    assert len(token.tokens) == 1
    assert isinstance(token.tokens[0], TimeoutToken)
    assert token.tokens[0] is timeout_token


def test_quasitemp_timeout_token_plus_not_temp_simple_token():
    simple_token = SimpleToken()
    token = TimeoutToken(1) + simple_token

    assert isinstance(token, SimpleToken)
    assert token is not simple_token
    assert len(token.tokens) == 2
    assert isinstance(token.tokens[0], TimeoutToken)
    assert token.tokens[1] is simple_token


def test_not_quasitemp_timeout_token_plus_not_temp_simple_token():
    simple_token = SimpleToken()
    timeout_token = TimeoutToken(1)
    token = timeout_token + simple_token

    assert isinstance(token, SimpleToken)
    assert token is not simple_token
    assert len(token.tokens) == 2
    assert isinstance(token.tokens[0], TimeoutToken)
    assert token.tokens[0] is timeout_token
    assert token.tokens[1] is simple_token


def test_quasitemp_timeout_token_plus_temp_simple_token_reverse():
    token = SimpleToken() + TimeoutToken(1)

    assert isinstance(token, SimpleToken)
    assert len(token.tokens) == 1
    assert isinstance(token.tokens[0], TimeoutToken)


def test_not_quasitemp_timeout_token_plus_temp_simple_token_reverse():
    timeout_token = TimeoutToken(1)
    token = SimpleToken() + timeout_token

    assert isinstance(token, SimpleToken)
    assert len(token.tokens) == 1
    assert isinstance(token.tokens[0], TimeoutToken)
    assert token.tokens[0] is timeout_token


def test_quasitemp_timeout_token_plus_not_temp_simple_token_reverse():
    simple_token = SimpleToken()
    token = simple_token + TimeoutToken(1)

    assert isinstance(token, SimpleToken)
    assert token is not simple_token
    assert len(token.tokens) == 2
    assert isinstance(token.tokens[1], TimeoutToken)
    assert token.tokens[0] is simple_token


def test_not_quasitemp_timeout_token_plus_not_temp_simple_token_reverse():
    simple_token = SimpleToken()
    timeout_token = TimeoutToken(1)
    token = simple_token + timeout_token

    assert isinstance(token, SimpleToken)
    assert token is not simple_token
    assert len(token.tokens) == 2
    assert isinstance(token.tokens[1], TimeoutToken)
    assert token.tokens[1] is timeout_token
    assert token.tokens[0] is simple_token


def test_timeout_is_more_important_than_cache():
    sleep_time = 0.0001
    inner_token = SimpleToken(cancelled=True)
    token = TimeoutToken(sleep_time, inner_token)

    for report in token.get_report(True), token.get_report(False):
        assert report is not None
        assert isinstance(report, CancellationReport)
        assert report.from_token is inner_token
        assert report.cause == CancelCause.CANCELLED

    sleep(sleep_time * 2)

    for report in token.get_report(True), token.get_report(False):
        assert report is not None
        assert isinstance(report, CancellationReport)
        assert report.from_token is token
        assert report.cause == CancelCause.SUPERPOWER
