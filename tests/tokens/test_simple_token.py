import pytest

from ctok.tokens.simple_token import SimpleToken


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


def test_change_attribute_cancelled_from_false_to_true():
    token = SimpleToken()
    token.cancelled = True
    assert token.cancelled == True


def test_change_attribute_cancelled_from_true_to_true():
    token = SimpleToken(cancelled=True)
    token.cancelled = True
    assert token.cancelled == True


def test_change_attribute_cancelled_from_true_to_false():
    token = SimpleToken(cancelled=True)

    with pytest.raises(ValueError):
        token.cancelled = False


def test_change_attribute_cancelled_from_false_to_false():
    token = SimpleToken()
    token.cancelled = False
    assert token.cancelled == False
