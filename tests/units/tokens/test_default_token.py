import sys

import pytest
import full_match

from cantok import DefaultToken, SimpleToken, ImpossibleCancelError


def test_dafault_token_is_not_cancelled_by_default():
    token = DefaultToken()

    assert bool(token)
    assert token.cancelled == False
    assert token.is_cancelled() == False
    assert token.keep_on() == True

    token.check()


def test_you_can_set_cancelled_attribute_as_false():
    token = DefaultToken()

    token.cancelled = False

    assert bool(token)
    assert token.cancelled == False
    assert token.is_cancelled() == False
    assert token.keep_on() == True

    token.check()


def test_you_cant_set_true_as_cancelled_attribute():
    token = DefaultToken()

    with pytest.raises(ImpossibleCancelError, match=full_match('You cannot cancel a default token.')):
        token.cancelled = True

    assert token.cancelled == False


def test_you_cannot_cancel_default_token_by_standard_way():
    token = DefaultToken()

    with pytest.raises(ImpossibleCancelError, match=full_match('You cannot cancel a default token.')):
        token.cancel()

    assert token.cancelled == False


def test_str_for_default_token():
    assert str(DefaultToken()) == '<DefaultToken (not cancelled)>'


@pytest.mark.skipif(sys.version_info >= (3, 10), reason='Format of this exception messages was changed.')
def test_you_cannot_neste_another_token_to_default_one_old_pythons():
    with pytest.raises(TypeError, match=full_match('__init__() takes 1 positional argument but 2 were given')):
        DefaultToken(SimpleToken())


@pytest.mark.skipif(sys.version_info < (3, 10), reason='Format of this exception messages was changed.')
def test_you_cannot_neste_another_token_to_default_one_new_pythons():
    with pytest.raises(TypeError, match=full_match('DefaultToken.__init__() takes 1 positional argument but 2 were given')):
        DefaultToken(SimpleToken())


def test_default_plus_default():
    empty_sum = DefaultToken() + DefaultToken()

    assert isinstance(empty_sum, SimpleToken)
    assert len(empty_sum.tokens) == 0


def test_default_plus_default_plus_default():
    empty_sum = DefaultToken() + DefaultToken() + DefaultToken()

    assert isinstance(empty_sum, SimpleToken)
    assert len(empty_sum.tokens) == 0
