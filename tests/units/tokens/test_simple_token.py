import pytest

from cantok.tokens.abstract.abstract_token import CancelCause, CancellationReport
from cantok import SimpleToken, TimeoutToken, ConditionToken, CancellationError


def test_just_created_token_without_arguments():
    assert SimpleToken().cancelled == False
    assert SimpleToken().is_cancelled() == False
    assert SimpleToken().keep_on() == True


def test_just_created_token_with_argument_cancelled():
    assert SimpleToken(cancelled=True).cancelled == True
    assert SimpleToken(cancelled=True).is_cancelled() == True
    assert SimpleToken(cancelled=True).keep_on() == False


@pytest.mark.parametrize('arguments,expected_cancelled_status', [
    ([SimpleToken(), SimpleToken().cancel()], True),
    ([SimpleToken()], False),
    ([SimpleToken().cancel()], True),
    ([SimpleToken(SimpleToken().cancel())], True),
    ([SimpleToken(), SimpleToken()], False),
    ([SimpleToken(), SimpleToken(), SimpleToken()], False),
    ([SimpleToken(), SimpleToken(), SimpleToken(), SimpleToken()], False),
])
def test_just_created_token_with_arguments(arguments, expected_cancelled_status):
    assert SimpleToken(*arguments).cancelled == expected_cancelled_status
    assert SimpleToken(*arguments).is_cancelled() == expected_cancelled_status
    assert SimpleToken(*arguments).keep_on() == (not expected_cancelled_status)


def test_stopped_token_is_not_going_on():
    token = SimpleToken()
    token.cancel()

    assert token.cancelled == True
    assert token.is_cancelled() == True
    assert token.keep_on() == False


def test_chain_with_simple_tokens():
    assert SimpleToken(SimpleToken(SimpleToken(SimpleToken(SimpleToken(cancelled=True))))).cancelled == True
    assert SimpleToken(SimpleToken(SimpleToken(SimpleToken(SimpleToken().cancel())))).cancelled == True
    assert SimpleToken(SimpleToken(SimpleToken(SimpleToken(SimpleToken())))).cancelled == False


def test_check_superpower_raised():
    token = SimpleToken()

    token.cancel()

    with pytest.raises(CancellationError):
        token.check()

    try:
        token.check()
    except CancellationError as e:
        assert type(e) is CancellationError
        assert str(e) == 'The token has been cancelled.'
        assert e.token is token


def test_check_superpower_raised_nested():
    nested_token = SimpleToken()
    token = SimpleToken(nested_token)

    nested_token.cancel()

    with pytest.raises(CancellationError):
        token.check()

    try:
        token.check()
    except CancellationError as e:
        assert type(e) is CancellationError
        assert str(e) == 'The token has been cancelled.'
        assert e.token is nested_token
        assert e.token.exception is type(e)


def test_get_report_cancelled():
    token = SimpleToken(cancelled=True)

    report = token.get_report()

    assert isinstance(report, CancellationReport)
    assert report.cause == CancelCause.CANCELLED
    assert report.from_token is token


@pytest.mark.parametrize(
    'cancelled_flag,cancelled_flag_nested,from_token_is_nested',
    [
        (True, True, False),
        (True, False, False),
        (False, True, True),
    ],
)
def test_get_report_cancelled_nested(cancelled_flag, cancelled_flag_nested, from_token_is_nested):
    nested_token = SimpleToken(cancelled=cancelled_flag_nested)
    token = SimpleToken(nested_token, cancelled=cancelled_flag)

    report = token.get_report()

    assert isinstance(report, CancellationReport)
    assert report.cause == CancelCause.CANCELLED
    if from_token_is_nested:
        assert report.from_token is nested_token
    else:
        assert report.from_token is token


def test_sum_of_2_temp_simple_tokens():
    token = SimpleToken() + SimpleToken()

    assert isinstance(token, SimpleToken)
    assert len(token.tokens) == 0


def test_sum_of_5_temp_simple_tokens():
    token = SimpleToken() + SimpleToken() + SimpleToken() + SimpleToken() + SimpleToken()

    assert isinstance(token, SimpleToken)
    assert len(token.tokens) == 0


def test_sum_of_1_temp_and_1_not_temp_simple_tokens():
    second_token = SimpleToken()
    result = SimpleToken() + second_token

    assert isinstance(result, SimpleToken)
    assert len(result.tokens) == 1
    assert result.tokens[0] is second_token


def test_sum_of_1_not_temp_and_1_temp_simple_tokens():
    first_token = SimpleToken()
    result = first_token + SimpleToken()

    assert isinstance(result, SimpleToken)
    assert len(result.tokens) == 1
    assert result.tokens[0] is first_token


def test_sum_of_2_not_temp_simple_tokens():
    first_token = SimpleToken()
    second_token = SimpleToken()
    result = first_token + second_token

    assert isinstance(result, SimpleToken)
    assert len(result.tokens) == 2
    assert result.tokens[0] is first_token
    assert result.tokens[1] is second_token


def test_sum_of_2_not_temp_simple_tokens_and_one_temp():
    first_token = SimpleToken()
    second_token = SimpleToken()
    result = first_token + second_token + SimpleToken()

    assert isinstance(result, SimpleToken)
    assert len(result.tokens) == 2
    assert result.tokens[0] is first_token
    assert result.tokens[1] is second_token


def test_sum_of_3_not_temp_simple_tokens():
    first_token = SimpleToken()
    second_token = SimpleToken()
    third_token = SimpleToken()
    result = first_token + second_token + third_token

    assert isinstance(result, SimpleToken)
    assert len(result.tokens) == 3
    assert result.tokens[0] is first_token
    assert result.tokens[1] is second_token
    assert result.tokens[2] is third_token


def test_sum_of_2_temp_timeout_tokens_throw_temp_simple_tokens():
    token = SimpleToken(TimeoutToken(1)) + SimpleToken(TimeoutToken(2))

    assert isinstance(token, SimpleToken)
    assert len(token.tokens) == 2

    assert isinstance(token.tokens[0], TimeoutToken)
    assert token.tokens[0].timeout == 1

    assert isinstance(token.tokens[1], TimeoutToken)
    assert token.tokens[1].timeout == 2


def test_sum_of_2_temp_timeout_tokens_throw_right_temp_simple_token():
    token = TimeoutToken(1) + SimpleToken(TimeoutToken(2))

    assert isinstance(token, SimpleToken)
    assert len(token.tokens) == 2

    assert isinstance(token.tokens[0], TimeoutToken)
    assert token.tokens[0].timeout == 1

    assert isinstance(token.tokens[1], TimeoutToken)
    assert token.tokens[1].timeout == 2


def test_sum_of_2_temp_timeout_tokens_throw_left_temp_simple_token():
    token = SimpleToken(TimeoutToken(1)) + TimeoutToken(2)

    assert isinstance(token, SimpleToken)
    assert len(token.tokens) == 2

    assert isinstance(token.tokens[0], TimeoutToken)
    assert token.tokens[0].timeout == 1

    assert isinstance(token.tokens[1], TimeoutToken)
    assert token.tokens[1].timeout == 2


def test_sum_of_2_not_temp_timeout_tokens_throw_temp_simple_tokens():
    first_timeout_token = TimeoutToken(1)
    second_timeout_token = TimeoutToken(2)
    token = SimpleToken(first_timeout_token) + SimpleToken(second_timeout_token)

    assert isinstance(token, SimpleToken)
    assert len(token.tokens) == 2

    assert token.tokens[0] is first_timeout_token
    assert isinstance(token.tokens[0], TimeoutToken)
    assert token.tokens[0].timeout == 1

    assert token.tokens[1] is second_timeout_token
    assert isinstance(token.tokens[1], TimeoutToken)
    assert token.tokens[1].timeout == 2


def test_sum_of_first_temp_and_second_not_temp_timeout_tokens_throw_temp_simple_tokens():
    second_timeout_token = TimeoutToken(2)
    token = SimpleToken(TimeoutToken(1)) + SimpleToken(second_timeout_token)

    assert isinstance(token, SimpleToken)
    assert len(token.tokens) == 2

    assert isinstance(token.tokens[0], TimeoutToken)
    assert token.tokens[0].timeout == 1

    assert token.tokens[1] is second_timeout_token
    assert isinstance(token.tokens[1], TimeoutToken)
    assert token.tokens[1].timeout == 2


def test_sum_of_first_not_temp_and_second_temp_timeout_tokens_throw_temp_simple_tokens():
    first_timeout_token = TimeoutToken(1)
    token = SimpleToken(first_timeout_token) + SimpleToken(TimeoutToken(2))

    assert isinstance(token, SimpleToken)
    assert len(token.tokens) == 2

    assert token.tokens[0] is first_timeout_token
    assert isinstance(token.tokens[0], TimeoutToken)
    assert token.tokens[0].timeout == 1

    assert isinstance(token.tokens[1], TimeoutToken)
    assert token.tokens[1].timeout == 2


def test_sum_of_temp_timeout_token_and_temp_condition_token_throw_temp_simple_tokens():
    token = SimpleToken(TimeoutToken(1)) + SimpleToken(ConditionToken(lambda: False))

    assert isinstance(token, SimpleToken)
    assert len(token.tokens) == 2
    assert token

    assert isinstance(token.tokens[0], TimeoutToken)
    assert token.tokens[0].timeout == 1

    assert isinstance(token.tokens[1], ConditionToken)


def test_sum_of_temp_condition_token_and_temp_timeout_token_throw_temp_simple_tokens():
    token = SimpleToken(ConditionToken(lambda: False)) + SimpleToken(TimeoutToken(1))

    assert isinstance(token, SimpleToken)
    assert len(token.tokens) == 2
    assert token

    assert isinstance(token.tokens[0], ConditionToken)

    assert isinstance(token.tokens[1], TimeoutToken)
    assert token.tokens[1].timeout == 1


def test_sum_of_not_temp_timeout_token_and_temp_condition_token_throw_temp_simple_tokens():
    timeout_token = TimeoutToken(1)
    token = SimpleToken(timeout_token) + SimpleToken(ConditionToken(lambda: False))

    assert isinstance(token, SimpleToken)
    assert len(token.tokens) == 2
    assert token

    assert token.tokens[0] is timeout_token
    assert isinstance(token.tokens[0], TimeoutToken)
    assert token.tokens[0].timeout == 1

    assert isinstance(token.tokens[1], ConditionToken)


def test_sum_of_temp_timeout_token_and_not_temp_condition_token_throw_temp_simple_tokens():
    condition_token = ConditionToken(lambda: False)
    token = SimpleToken(TimeoutToken(1)) + SimpleToken(condition_token)

    assert isinstance(token, SimpleToken)
    assert len(token.tokens) == 2
    assert token

    assert isinstance(token.tokens[0], TimeoutToken)
    assert token.tokens[0].timeout == 1

    assert isinstance(token.tokens[1], ConditionToken)
    assert token.tokens[1] is condition_token


def test_sum_of_not_temp_condition_token_and_temp_timeout_token_throw_temp_simple_tokens():
    condition_token = ConditionToken(lambda: False)
    token = SimpleToken(condition_token) + SimpleToken(TimeoutToken(1))

    assert isinstance(token, SimpleToken)
    assert len(token.tokens) == 2
    assert token

    assert isinstance(token.tokens[0], ConditionToken)
    assert token.tokens[0] is condition_token

    assert isinstance(token.tokens[1], TimeoutToken)
    assert token.tokens[1].timeout == 1


def test_sum_of_not_temp_timeout_token_and_not_temp_condition_token_throw_temp_simple_tokens():
    timeout_token = TimeoutToken(1)
    condition_token = ConditionToken(lambda: False)
    token = SimpleToken(timeout_token) + SimpleToken(condition_token)

    assert isinstance(token, SimpleToken)
    assert len(token.tokens) == 2
    assert token

    assert token.tokens[0] is timeout_token
    assert isinstance(token.tokens[0], TimeoutToken)
    assert token.tokens[0].timeout == 1

    assert token.tokens[1] is condition_token
    assert isinstance(token.tokens[1], ConditionToken)


def test_sum_of_not_temp_condition_token_and_not_temp_timeout_token_throw_temp_simple_tokens():
    timeout_token = TimeoutToken(1)
    condition_token = ConditionToken(lambda: False)
    token = SimpleToken(condition_token) + SimpleToken(timeout_token)

    assert isinstance(token, SimpleToken)
    assert len(token.tokens) == 2
    assert token

    assert token.tokens[0] is condition_token
    assert isinstance(token.tokens[0], ConditionToken)

    assert token.tokens[1] is timeout_token
    assert isinstance(token.tokens[1], TimeoutToken)
    assert token.tokens[1].timeout == 1
