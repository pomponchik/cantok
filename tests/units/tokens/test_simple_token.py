import pytest

from cantok.tokens.abstract_token import CancelCause, CancellationReport
from cantok import SimpleToken, CancellationError


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
