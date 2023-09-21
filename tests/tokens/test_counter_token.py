import pytest

from ctok.tokens.counter_token import CounterToken


@pytest.mark.parametrize(
    'iterations',
    [
        0,
        1,
        5,
        15,
    ],
)
def test_counter(iterations):
    token = CounterToken(iterations)
    counter = 0

    while not token.cancelled:
        counter += 1

    assert counter == iterations


def test_counter_less_than_zero():
    with pytest.raises(ValueError):
        CounterToken(-1)
