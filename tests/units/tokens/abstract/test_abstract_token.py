import asyncio
from functools import partial
from time import perf_counter, sleep
from threading import Thread

import pytest
import full_match

from cantok.tokens.abstract.abstract_token import AbstractToken, CancelCause, CancellationReport
from cantok import SimpleToken, ConditionToken, TimeoutToken, CounterToken, DefaultToken, CancellationError


ALL_TOKEN_CLASSES = [SimpleToken, ConditionToken, TimeoutToken, CounterToken]
ALL_SUPERPOWER_TOKEN_CLASSES = [ConditionToken, TimeoutToken, CounterToken]
ALL_ARGUMENTS_FOR_TOKEN_CLASSES = [tuple(), (lambda: False, ), (15, ), (15, )]
ALL_CANCELLING_ARGUMENTS_FOR_TOKEN_CLASSES_WITH_SUPERPOWERS = [(lambda: True, ), (0, ), (0, )]
ALL_NOT_CANCELLING_ARGUMENTS_FOR_TOKEN_CLASSES_WITH_SUPERPOWERS = [(lambda: False, ), (15, ), (15, )]
ALL_TOKENS_FABRICS = [partial(token_class, *arguments) for token_class, arguments in zip(ALL_TOKEN_CLASSES, ALL_ARGUMENTS_FOR_TOKEN_CLASSES)]
ALL_TOKENS_FABRICS_WITH_CANCELLING_SUPERPOWER = [partial(token_class, *arguments) for token_class, arguments in zip(ALL_SUPERPOWER_TOKEN_CLASSES, ALL_CANCELLING_ARGUMENTS_FOR_TOKEN_CLASSES_WITH_SUPERPOWERS)]
ALL_TOKENS_FABRICS_WITH_NOT_CANCELLING_SUPERPOWER = [partial(token_class, *arguments) for token_class, arguments in zip(ALL_SUPERPOWER_TOKEN_CLASSES, ALL_NOT_CANCELLING_ARGUMENTS_FOR_TOKEN_CLASSES_WITH_SUPERPOWERS)]


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
        with pytest.raises(ValueError, match='You cannot restore a cancelled token.'):
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
def test_set_cancelled_false_if_this_token_is_not_cancelled_but_nested_token_is(token_fabric):
    token = token_fabric(SimpleToken(cancelled=True))

    with pytest.raises(ValueError, match=full_match('You cannot restore a cancelled token.')):
        token.cancelled = False


@pytest.mark.parametrize(
    'token_fabric',
    ALL_TOKENS_FABRICS + [DefaultToken],
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
def test_add_not_temp_tokens(first_token_fabric, second_token_fabric):
    first_token = first_token_fabric()
    second_token = second_token_fabric()

    tokens_sum = first_token + second_token

    assert isinstance(tokens_sum, SimpleToken)
    assert len(tokens_sum.tokens) == 2
    assert tokens_sum.tokens[0] is first_token
    assert tokens_sum.tokens[1] is second_token


@pytest.mark.parametrize(
    ['first_token_class', 'first_arguments'],
    [
        (TimeoutToken, [15]),
        (ConditionToken, [lambda: False]),
        (CounterToken, [15]),
    ],
)
@pytest.mark.parametrize(
    ['second_token_class', 'second_arguments'],
    [
        (TimeoutToken, [15]),
        (ConditionToken, [lambda: False]),
        (CounterToken, [15]),
    ],
)
def test_add_temp_tokens(first_token_class, second_token_class, first_arguments, second_arguments):
    tokens_sum = first_token_class(*first_arguments) + second_token_class(*second_arguments)

    if not (first_token_class is TimeoutToken and second_token_class is TimeoutToken):
        assert isinstance(tokens_sum, first_token_class)
        assert len(tokens_sum.tokens) == 1
        assert isinstance(tokens_sum.tokens[0], second_token_class)
        assert len(tokens_sum.tokens[0].tokens) == 0
    else:
        assert isinstance(tokens_sum, TimeoutToken)
        assert len(tokens_sum.tokens) == 0


@pytest.mark.parametrize(
    ['first_token_class', 'first_arguments'],
    [
        (TimeoutToken, [15]),
        (ConditionToken, [lambda: False]),
        (CounterToken, [15]),
    ],
)
@pytest.mark.parametrize(
    ['second_token_class', 'second_arguments'],
    [
        (TimeoutToken, [15]),
        (ConditionToken, [lambda: False]),
        (CounterToken, [15]),
    ],
)
def test_add_not_temp_token_and_temp_token(first_token_class, second_token_class, first_arguments, second_arguments):
    first_token = first_token_class(*first_arguments)
    tokens_sum = first_token + second_token_class(*second_arguments)

    if first_token_class is TimeoutToken and second_token_class is TimeoutToken:
        assert tokens_sum is first_token
        assert not tokens_sum.tokens
    else:
        assert isinstance(tokens_sum, second_token_class)
        assert len(tokens_sum.tokens) == 1
        assert isinstance(tokens_sum.tokens[0], first_token_class)
        assert len(tokens_sum.tokens[0].tokens) == 0


@pytest.mark.parametrize(
    ['first_token_class', 'first_arguments'],
    [
        (TimeoutToken, [15]),
        (ConditionToken, [lambda: False]),
        (CounterToken, [15]),
    ],
)
@pytest.mark.parametrize(
    ['second_token_class', 'second_arguments'],
    [
        (TimeoutToken, [15]),
        (ConditionToken, [lambda: False]),
        (CounterToken, [15]),
    ],
)
def test_add_temp_token_and_not_temp_token(first_token_class, second_token_class, first_arguments, second_arguments):
    second_token = second_token_class(*second_arguments)
    tokens_sum = first_token_class(*first_arguments) + second_token

    if first_token_class is TimeoutToken and second_token_class is TimeoutToken:
        assert isinstance(tokens_sum, TimeoutToken)
        assert len(tokens_sum.tokens) == 0
    else:
        assert isinstance(tokens_sum, first_token_class)
        assert len(tokens_sum.tokens) == 1
        assert isinstance(tokens_sum.tokens[0], second_token_class)
        assert len(tokens_sum.tokens[0].tokens) == 0


@pytest.mark.parametrize(
    'first_token_fabric',
    ALL_TOKENS_FABRICS_WITH_NOT_CANCELLING_SUPERPOWER,
)
@pytest.mark.parametrize(
    'second_token_fabric',
    ALL_TOKENS_FABRICS_WITH_NOT_CANCELLING_SUPERPOWER,
)
@pytest.mark.parametrize(
    'third_token_fabric',
    ALL_TOKENS_FABRICS_WITH_NOT_CANCELLING_SUPERPOWER,
)
def test_add_three_tokens_except_simple_token(first_token_fabric, second_token_fabric, third_token_fabric):
    first_token = first_token_fabric()
    second_token = second_token_fabric()
    third_token = third_token_fabric()

    tokens_sum = first_token + second_token + third_token

    assert isinstance(tokens_sum, SimpleToken)
    assert len(tokens_sum.tokens) == 3
    assert tokens_sum.tokens[0] is first_token
    assert tokens_sum.tokens[1] is second_token
    assert tokens_sum.tokens[2] is third_token


@pytest.mark.parametrize(
    'first_token_fabric',
    ALL_TOKENS_FABRICS_WITH_NOT_CANCELLING_SUPERPOWER,
)
def test_add_another_token_and_temp_simple_token(first_token_fabric):
    first_token = first_token_fabric()

    tokens_sum = first_token + SimpleToken()

    assert isinstance(tokens_sum, SimpleToken)
    assert len(tokens_sum.tokens) == 1
    assert tokens_sum.tokens[0] is first_token


@pytest.mark.parametrize(
    'second_token_fabric',
    ALL_TOKENS_FABRICS_WITH_NOT_CANCELLING_SUPERPOWER,
)
def test_add_temp_simple_token_and_another_token(second_token_fabric):
    second_token = second_token_fabric()

    tokens_sum = SimpleToken() + second_token

    assert isinstance(tokens_sum, SimpleToken)
    assert len(tokens_sum.tokens) == 1
    assert tokens_sum.tokens[0] is second_token


@pytest.mark.parametrize(
    'first_token_fabric',
    ALL_TOKENS_FABRICS_WITH_NOT_CANCELLING_SUPERPOWER,
)
def test_add_another_token_and_not_temp_simple_token(first_token_fabric):
    simple_token = SimpleToken()
    first_token = first_token_fabric()

    tokens_sum = first_token + simple_token

    assert isinstance(tokens_sum, SimpleToken)
    assert len(tokens_sum.tokens) == 2
    assert tokens_sum.tokens[0] is first_token
    assert tokens_sum.tokens[1] is simple_token


@pytest.mark.parametrize(
    'second_token_fabric',
    [x for x in ALL_TOKENS_FABRICS if x is not SimpleToken],
)
def test_add_not_temp_simple_token_and_another_token(second_token_fabric):
    simple_token = SimpleToken()
    second_token = second_token_fabric()

    tokens_sum = simple_token + second_token

    assert isinstance(tokens_sum, SimpleToken)
    assert len(tokens_sum.tokens) == 2
    assert tokens_sum.tokens[0] is simple_token
    assert tokens_sum.tokens[1] is second_token


@pytest.mark.parametrize(
    'second_token_fabric',
    ALL_TOKENS_FABRICS,
)
def test_add_tokens_and_first_is_default_token(second_token_fabric):
    first_token = DefaultToken()
    second_token = second_token_fabric()

    tokens_sum = first_token + second_token

    assert isinstance(tokens_sum, SimpleToken)
    assert len(tokens_sum.tokens) == 1
    assert tokens_sum.tokens[0] is second_token


@pytest.mark.parametrize(
    'first_token_fabric',
    ALL_TOKENS_FABRICS,
)
def test_add_tokens_and_second_one_is_default_token(first_token_fabric):
    first_token = first_token_fabric()
    second_token = DefaultToken()

    tokens_sum = first_token + second_token

    assert isinstance(tokens_sum, SimpleToken)
    assert len(tokens_sum.tokens) == 1
    assert tokens_sum.tokens[0] is first_token


@pytest.mark.parametrize(
    'token_fabric',
    ALL_TOKENS_FABRICS + [DefaultToken],
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
    with pytest.raises(TypeError, match='Cancellation Token can only be combined with another Cancellation Token.'):
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
    ALL_TOKENS_FABRICS + [DefaultToken],
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
    ALL_TOKENS_FABRICS + [DefaultToken],
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
    ALL_TOKENS_FABRICS + [DefaultToken],
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
    ],
)
@pytest.mark.parametrize(
    'token_fabric',
    ALL_TOKENS_FABRICS + [DefaultToken],
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
    ALL_TOKENS_FABRICS + [DefaultToken],
)
def test_async_wait_timeout(token_fabric):
    timeout = 0.0001
    token = token_fabric()

    with pytest.raises(TimeoutToken.exception):
        asyncio.run(token.wait(timeout=timeout))


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

    async def runner(token):
        coroutines = [cancel_with_timeout(token), token.wait(), ]
        return await asyncio.gather(*coroutines)

    start_time = perf_counter()
    asyncio.run(runner(token))
    finish_time = perf_counter()

    assert not token
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
    thread.join()
    finish_time = perf_counter()

    assert finish_time - start_time >= timeout


@pytest.mark.parametrize(
    'token_fabric',
    ALL_TOKENS_FABRICS,
)
def test_insert_default_token_to_another_tokens(token_fabric):
    token = token_fabric(DefaultToken())

    assert not isinstance(token, DefaultToken)
    assert len(token.tokens) == 0


@pytest.mark.parametrize(
    'first_token_fabric',
    ALL_TOKENS_FABRICS,
)
@pytest.mark.parametrize(
    'second_token_fabric',
    ALL_TOKENS_FABRICS,
)
@pytest.mark.parametrize(
    'action',
    [
        lambda x: x.cancelled,
        lambda x: x.keep_on(),
        lambda x: bool(x),
        lambda x: bool(x),
        lambda x: x.is_cancelled(),
        lambda x: x.get_report(True),
        lambda x: x.get_report(False),
    ],
)
def test_report_cache_is_working_in_simple_case(first_token_fabric, second_token_fabric, action):
    token = first_token_fabric(second_token_fabric(cancelled=True))

    assert token.cached_report is None

    action(token)

    cached_report = token.cached_report

    assert cached_report is not None
    assert isinstance(cached_report, CancellationReport)
    assert cached_report.from_token.is_cancelled()
    assert cached_report.cause == CancelCause.CANCELLED

    assert token.get_report(True) is cached_report
    assert token.get_report(False) is cached_report


@pytest.mark.parametrize(
    'first_token_fabric',
    ALL_TOKENS_FABRICS,
)
@pytest.mark.parametrize(
    'second_token_fabric',
    ALL_TOKENS_FABRICS,
)
@pytest.mark.parametrize(
    'action',
    [
        lambda x: x.cancelled,
        lambda x: x.keep_on(),
        lambda x: bool(x),
        lambda x: bool(x),
        lambda x: x.is_cancelled(),
        lambda x: x.get_report(True),
        lambda x: x.get_report(False),
    ],
)
def test_cache_is_using_after_self_flag(first_token_fabric, second_token_fabric, action):
    token = first_token_fabric(second_token_fabric(cancelled=True))

    action(token)

    cached_report = token.cached_report

    token.cancel()

    for new_report in token.get_report(True), token.get_report(False):
        assert new_report is not cached_report
        assert new_report is not None
        assert isinstance(new_report, CancellationReport)
        assert new_report.from_token.is_cancelled()
        assert new_report.cause == CancelCause.CANCELLED


@pytest.mark.parametrize(
    'first_token_fabric',
    ALL_TOKENS_FABRICS_WITH_CANCELLING_SUPERPOWER,
)
@pytest.mark.parametrize(
    'second_token_fabric',
    ALL_TOKENS_FABRICS_WITH_CANCELLING_SUPERPOWER,
)
@pytest.mark.parametrize(
    'action',
    [
        lambda x: x.cancelled,
        lambda x: x.keep_on(),
        lambda x: bool(x),
        lambda x: bool(x),
        lambda x: x.is_cancelled(),
        lambda x: x.get_report(True),
        lambda x: x.get_report(False),
    ],
)
def test_superpower_is_more_important_than_cache(first_token_fabric, second_token_fabric, action):
    token = first_token_fabric(second_token_fabric(cancelled=True))

    for report in token.get_report(True), token.get_report(False):
        assert report is not None
        assert isinstance(report, CancellationReport)
        assert report.from_token is token
        assert report.cause == CancelCause.SUPERPOWER

    action(token)

    for report in token.get_report(True), token.get_report(False):
        assert report is not None
        assert isinstance(report, CancellationReport)
        assert report.from_token is token
        assert report.cause == CancelCause.SUPERPOWER

    token.cancel()

    for report in token.get_report(True), token.get_report(False):
        assert report is not None
        assert isinstance(report, CancellationReport)
        assert report.from_token is token
        assert report.cause == CancelCause.CANCELLED


@pytest.mark.parametrize(
    'token_fabric',
    ALL_TOKENS_FABRICS,
)
def test_just_neste_temp_simple_token_to_another_token(token_fabric):
    token = token_fabric(SimpleToken())

    assert len(token.tokens) == 1
    assert isinstance(token.tokens[0], SimpleToken)
    assert token


@pytest.mark.parametrize(
    'token_fabric',
    ALL_TOKENS_FABRICS,
)
def test_any_token_plus_temp_cancelled_simple_token_gives_cancelled_simple_token(token_fabric):
    token = token_fabric() + SimpleToken(cancelled=True)

    assert isinstance(token, SimpleToken)
    assert len(token.tokens) == 0
    assert not token


@pytest.mark.parametrize(
    'token_fabric',
    ALL_TOKENS_FABRICS,
)
def test_any_token_plus_cancelled_simple_token_gives_cancelled_simple_token(token_fabric):
    simple_token = SimpleToken(cancelled=True)
    token = token_fabric() + simple_token

    assert isinstance(token, SimpleToken)
    assert len(token.tokens) == 0
    assert not token
