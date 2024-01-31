import asyncio
from time import sleep, perf_counter

import pytest

from cantok.tokens.abstract_token import CancelCause, CancellationReport
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
    with pytest.raises(ValueError):
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
    assert TimeoutToken(5, monotonic=False).text_representation_of_extra_kwargs() == 'monotonic=False'
    assert TimeoutToken(5, monotonic=True).text_representation_of_extra_kwargs() == 'monotonic=True'
    assert TimeoutToken(5).text_representation_of_extra_kwargs() == 'monotonic=False'


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


def test_run_async_two_timeouts():
    sleep_duration = 0.0001
    number_of_tokens = 10

    tokens = [TimeoutToken(sleep_duration) for x in range(number_of_tokens)]

    async def runner():
        return await asyncio.gather(*(x.wait() for x in tokens))

    start_time = perf_counter()
    asyncio.run(runner())
    finish_time = perf_counter()

    assert (finish_time - start_time) < (sleep_duration * number_of_tokens)


def test_timeout_wait():
    sleep_duration = 1
    token = TimeoutToken(sleep_duration)

    start_time = perf_counter()
    token.wait()
    finish_time = perf_counter()

    assert sleep_duration <= finish_time - start_time
