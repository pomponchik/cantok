import asyncio
from functools import partial
from time import perf_counter, sleep
from threading import Thread
from queue import Queue

import pytest

from cantok.tokens.abstract_token import AbstractToken, CancelCause, CancellationReport, AngryAwaitable
from cantok import SimpleToken, ConditionToken, TimeoutToken, CounterToken, CancellationError
from cantok.errors import SynchronousWaitingError


ALL_TOKEN_CLASSES = [SimpleToken, ConditionToken, TimeoutToken, CounterToken]
ALL_ARGUMENTS_FOR_TOKEN_CLASSES = [tuple(), (lambda: False, ), (15, ), (15, )]
ALL_TOKENS_FABRICS = [partial(token_class, *arguments) for token_class, arguments in zip(ALL_TOKEN_CLASSES, ALL_ARGUMENTS_FOR_TOKEN_CLASSES)]



def test_cant_instantiate_abstract_token():
    with pytest.raises(TypeError):
        AbstractToken()


@pytest.mark.parametrize(
    'cancelled_flag',
    [True, False],
)
@pytest.mark.parametrize(
    'token_fabric',
    ALL_TOKENS_FABRICS,
)
def test_cancelled_true_as_parameter(token_fabric, cancelled_flag):
    token = token_fabric(cancelled=cancelled_flag)
    assert token.cancelled == cancelled_flag
    assert token.is_cancelled() == cancelled_flag
    assert token.keep_on() == (not cancelled_flag)

    if cancelled_flag:
        with pytest.raises(CancellationError):
            token.check()
    else:
        token.check()


@pytest.mark.parametrize(
    'first_cancelled_flag,second_cancelled_flag,expected_value',
    [
        (True, True, True),
        (False, False, False),
        (False, True, True),
        (True, False, None),
    ],
)
@pytest.mark.parametrize(
    'token_fabric',
    ALL_TOKENS_FABRICS,
)
def test_change_attribute_cancelled(token_fabric, first_cancelled_flag, second_cancelled_flag, expected_value):
    token = token_fabric(cancelled=first_cancelled_flag)

    if expected_value is None:
        with pytest.raises(ValueError):
            token.cancelled = second_cancelled_flag

    else:
        token.cancelled = second_cancelled_flag
        assert token.cancelled == expected_value
        assert token.is_cancelled() == expected_value
        assert token.keep_on() == (not expected_value)

        if second_cancelled_flag:
            with pytest.raises(CancellationError):
                token.check()
        else:
            token.check()


@pytest.mark.parametrize(
    'token_fabric',
    ALL_TOKENS_FABRICS,
)
def test_repr(token_fabric):
    token = token_fabric()

    superpower_text = token.text_representation_of_superpower()
    extra_kwargs_text = token.text_representation_of_extra_kwargs()

    elements = ', '.join([x for x in (superpower_text, extra_kwargs_text) if x])

    assert repr(token) == type(token).__name__ + f'({elements})'


@pytest.mark.parametrize(
    'token_fabric',
    ALL_TOKENS_FABRICS,
)
def test_repr_with_another_token(token_fabric):
    nested_token = token_fabric()
    token = token_fabric(nested_token)

    superpower_text = token.text_representation_of_superpower()
    extra_kwargs_text = token.text_representation_of_extra_kwargs()

    assert repr(token) == type(token).__name__ + '(' + ('' if not superpower_text else f'{superpower_text}, ') + repr(nested_token) + (', ' + extra_kwargs_text if extra_kwargs_text else '') + ')'


@pytest.mark.parametrize(
    'token_fabric',
    ALL_TOKENS_FABRICS,
)
def test_str(token_fabric):
    token = token_fabric()

    assert str(token) == '<' + type(token).__name__ + ' (not cancelled)>'

    token.cancel()

    assert str(token) == '<' + type(token).__name__ + ' (cancelled)>'


@pytest.mark.parametrize(
    'first_token_fabric',
    ALL_TOKENS_FABRICS,
)
@pytest.mark.parametrize(
    'second_token_fabric',
    ALL_TOKENS_FABRICS,
)
def test_add_tokens(first_token_fabric, second_token_fabric):
    first_token = first_token_fabric()
    second_token = second_token_fabric()

    tokens_sum = first_token + second_token

    assert isinstance(tokens_sum, SimpleToken)
    assert len(tokens_sum.tokens) == 2
    assert tokens_sum.tokens[0] is first_token
    assert tokens_sum.tokens[1] is second_token


@pytest.mark.parametrize(
    'token_fabric',
    ALL_TOKENS_FABRICS,
)
@pytest.mark.parametrize(
    'another_object',
    [
        1,
        'kek',
        '',
        None,
    ],
)
def test_add_token_and_not_token(token_fabric, another_object):
    with pytest.raises(TypeError):
        token_fabric() + another_object

    with pytest.raises(TypeError):
        another_object + token_fabric()


@pytest.mark.parametrize(
    'token_fabric',
    ALL_TOKENS_FABRICS,
)
def test_check_cancelled_token(token_fabric):
    token = token_fabric()
    token.cancel()

    with pytest.raises(CancellationError):
        token.check()

    try:
        token.check()
    except CancellationError as e:
        assert type(e) is CancellationError
        assert e.token is token


@pytest.mark.parametrize(
    'token_fabric',
    ALL_TOKENS_FABRICS,
)
def test_check_superpower_not_raised(token_fabric):
    token = token_fabric()

    assert token.check() is None


@pytest.mark.parametrize(
    'token_fabric_1',
    ALL_TOKENS_FABRICS,
)
@pytest.mark.parametrize(
    'token_fabric_2',
    ALL_TOKENS_FABRICS,
)
def test_check_superpower_not_raised_nested(token_fabric_1, token_fabric_2):
    token = token_fabric_1(token_fabric_2())

    assert token.check() is None


@pytest.mark.parametrize(
    'token_fabric_1',
    ALL_TOKENS_FABRICS,
)
@pytest.mark.parametrize(
    'token_fabric_2',
    ALL_TOKENS_FABRICS,
)
def test_check_cancelled_token_nested(token_fabric_1, token_fabric_2):
    nested_token = token_fabric_1()
    token = token_fabric_2(nested_token)
    nested_token.cancel()

    with pytest.raises(CancellationError):
        token.check()

    try:
        token.check()
    except CancellationError as e:
        assert type(e) is CancellationError
        assert e.token is nested_token


@pytest.mark.parametrize(
    'token_fabric',
    ALL_TOKENS_FABRICS,
)
def test_get_report_not_cancelled(token_fabric):
    token = token_fabric()
    report = token.get_report()

    assert isinstance(report, CancellationReport)
    assert report.cause == CancelCause.NOT_CANCELLED
    assert report.from_token is token


@pytest.mark.parametrize(
    'token_fabric',
    ALL_TOKENS_FABRICS,
)
def test_get_report_not_cancelled_nested(token_fabric):
    token = token_fabric(token_fabric())
    report = token.get_report()

    assert isinstance(report, CancellationReport)
    assert report.cause == CancelCause.NOT_CANCELLED
    assert report.from_token is token


@pytest.mark.parametrize(
    'token_fabric_1',
    ALL_TOKENS_FABRICS,
)
@pytest.mark.parametrize(
    'token_fabric_2',
    ALL_TOKENS_FABRICS,
)
def test_get_report_cancelled(token_fabric_1, token_fabric_2):
    nested_token = token_fabric_1()
    token = token_fabric_2(nested_token)
    nested_token.cancel()
    report = token.get_report()

    assert isinstance(report, CancellationReport)
    assert report.cause == CancelCause.CANCELLED
    assert report.from_token is nested_token


@pytest.mark.parametrize(
    'token_fabric',
    ALL_TOKENS_FABRICS,
)
def test_type_conversion_not_cancelled(token_fabric):
    token = token_fabric()

    assert token
    assert bool(token)


@pytest.mark.parametrize(
    'token_fabric',
    ALL_TOKENS_FABRICS,
)
def test_type_conversion_cancelled(token_fabric):
    token = token_fabric(cancelled=True)

    assert not token
    assert not bool(token)


@pytest.mark.parametrize(
    'cancelled_flag_nested_token, cancelled_flag_token',
    [
        (True, True),
        (True, False),
        (False, True),
        (False, False),
    ],
)
@pytest.mark.parametrize(
    'token_fabric_1',
    ALL_TOKENS_FABRICS,
)
@pytest.mark.parametrize(
    'token_fabric_2',
    ALL_TOKENS_FABRICS,
)
def test_repr_if_nested_token_is_cancelled(token_fabric_1, token_fabric_2, cancelled_flag_nested_token, cancelled_flag_token):
    nested_token = token_fabric_1(cancelled=cancelled_flag_nested_token)
    token = token_fabric_2(nested_token, cancelled=cancelled_flag_token)

    assert ('cancelled' in repr(token).replace(repr(nested_token), '')) == cancelled_flag_token
    assert ('cancelled' in repr(nested_token)) == cancelled_flag_nested_token


@pytest.mark.parametrize(
    'parameters',
    [
        {'step': -1},
        {'step': -1, 'timeout': -1},
        {'step': -1, 'timeout': 0},
        {'timeout': -1},
        {'step': 1, 'timeout': -1},
        {'step': -1, 'timeout': 1},
        {'step': 2, 'timeout': 1},
        {'step': -1, 'is_async': True},
        {'step': -1, 'timeout': -1, 'is_async': True},
        {'step': -1, 'timeout': 0, 'is_async': True},
        {'timeout': -1, 'is_async': True},
        {'step': 1, 'timeout': -1, 'is_async': True},
        {'step': -1, 'timeout': 1, 'is_async': True},
        {'step': 2, 'timeout': 1, 'is_async': True},
        {'step': -1, 'is_async': False},
        {'step': -1, 'timeout': -1, 'is_async': False},
        {'step': -1, 'timeout': 0, 'is_async': False},
        {'timeout': -1, 'is_async': False},
        {'step': 1, 'timeout': -1, 'is_async': False},
        {'step': -1, 'timeout': 1, 'is_async': False},
        {'step': 2, 'timeout': 1, 'is_async': False},
    ],
)
@pytest.mark.parametrize(
    'token_fabric',
    ALL_TOKENS_FABRICS,
)
@pytest.mark.parametrize(
    'do_await',
    [
        True,
        False,
    ],
)
def test_wait_wrong_parameters(token_fabric, parameters, do_await):
    token = token_fabric()

    with pytest.raises(ValueError):
        if do_await:
            asyncio.run(token.wait(**parameters))
        else:
            token.wait(**parameters)


@pytest.mark.parametrize(
    'token_fabric',
    ALL_TOKENS_FABRICS,
)
def test_async_wait_timeout(token_fabric):
    timeout = 0.0001
    token = token_fabric()

    with pytest.raises(TimeoutToken.exception):
        asyncio.run(token.wait(timeout=timeout, is_async=True))


@pytest.mark.parametrize(
    'token_fabric',
    ALL_TOKENS_FABRICS,
)
def test_sync_wait_timeout(token_fabric):
    timeout = 0.0001
    token = token_fabric()

    with pytest.raises(TimeoutToken.exception):
        token.wait(timeout=timeout)


@pytest.mark.parametrize(
    'token_fabric',
    ALL_TOKENS_FABRICS,
)
def test_async_wait_with_cancel(token_fabric):
    timeout = 0.001
    token = token_fabric()

    async def cancel_with_timeout(token):
        await asyncio.sleep(timeout)
        token.cancel()

    async def runner():
        return await asyncio.gather(token.wait(is_async=True), cancel_with_timeout(token))

    start_time = perf_counter()
    asyncio.run(runner())
    finish_time = perf_counter()

    assert finish_time - start_time >= timeout


@pytest.mark.parametrize(
    'token_fabric',
    ALL_TOKENS_FABRICS,
)
def test_sync_wait_with_cancel(token_fabric):
    timeout = 0.001
    token = token_fabric()

    def cancel_with_timeout(token):
        sleep(timeout)
        token.cancel()

    start_time = perf_counter()
    thread = Thread(target=cancel_with_timeout, args=(token,))
    thread.start()
    token.wait()
    finish_time = perf_counter()

    assert finish_time - start_time >= timeout


def test_pseudo_awaitable():
    with pytest.raises(SynchronousWaitingError):
        asyncio.run(AngryAwaitable())


@pytest.mark.parametrize(
    'token_fabric',
    ALL_TOKENS_FABRICS,
)
def test_sync_run_returns_angry_awaitable(token_fabric):
    token = token_fabric(cancelled=True)

    assert isinstance(token.wait(timeout=0.001), AngryAwaitable)
