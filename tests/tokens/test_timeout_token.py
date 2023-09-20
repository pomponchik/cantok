from time import sleep

import pytest

from ctok import TimeoutToken


@pytest.mark.parametrize(
    'zero_timeout',
    [0, 0.0],
)
def test_zero_timeout(zero_timeout):
    token = TimeoutToken(zero_timeout)

    sleep(1)

    assert token.cancelled == True
    assert token.cancelled == True
    assert token.is_cancelled() == True
    assert token.is_cancelled() == True
    assert token.keep_on() == False
    assert token.keep_on() == False
