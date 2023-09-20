from time import sleep

import pytest

from ctok import TimeoutToken


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
