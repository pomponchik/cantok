from functools import partial

import pytest

from cantok.tokens.abstract_token import AbstractToken
from cantok import SimpleToken, ConditionToken, TimeoutToken, CounterToken


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


@pytest.mark.parametrize(
    'token_fabric',
    ALL_TOKENS_FABRICS,
)
def test_repr(token_fabric):
    token = token_fabric()
    superpower_text = token.text_representation_of_superpower()
    extra_kwargs_text = token.text_representation_of_extra_kwargs()

    assert repr(token) == type(token).__name__ + '(' + ('' if not superpower_text else f'{superpower_text}, ') + 'cancelled=False' + (', ' + extra_kwargs_text if extra_kwargs_text else '') + ')'


@pytest.mark.parametrize(
    'token_fabric',
    ALL_TOKENS_FABRICS,
)
def test_repr_with_another_token(token_fabric):
    another_token = token_fabric()
    token = token_fabric(another_token)

    superpower_text = token.text_representation_of_superpower()
    extra_kwargs_text = token.text_representation_of_extra_kwargs()

    assert repr(token) == type(token).__name__ + '(' + ('' if not superpower_text else f'{superpower_text}, ') + repr(another_token) + ', ' + 'cancelled=False' + (', ' + extra_kwargs_text if extra_kwargs_text else '') + ')'


@pytest.mark.parametrize(
    'token_fabric',
    ALL_TOKENS_FABRICS,
)
def test_str(token_fabric):
    token = token_fabric()

    assert str(token) == '<' + type(token).__name__ + ' (not cancelled)>'

    token.cancel()

    assert str(token) == '<' + type(token).__name__ + ' (cancelled)>'
