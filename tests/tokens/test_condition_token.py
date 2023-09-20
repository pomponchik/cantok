from functools import partial

import pytest

from ctok import SimpleToken, ConditionToken


def test_condition_counter():
    loop_size = 5
    def condition():
        for number in range(loop_size):
            yield False
        while True:
            yield True

    token = ConditionToken(partial(next, iter(condition())))

    counter = 0
    while not token.cancelled:
        counter += 1

    assert counter == loop_size


def test_condition_false():
    assert ConditionToken(lambda: False).cancelled == False
    assert ConditionToken(lambda: False).is_cancelled() == False
    assert ConditionToken(lambda: False).keep_on() == True


def test_condition_true():
    assert ConditionToken(lambda: True).cancelled == True
    assert ConditionToken(lambda: True).is_cancelled() == True
    assert ConditionToken(lambda: True).keep_on() == False


@pytest.mark.parametrize('arguments,expected_cancelled_status', [
    ([SimpleToken(), SimpleToken().cancel()], True),
    ([SimpleToken(), ConditionToken(lambda: True)], True),
    ([ConditionToken(lambda: False), ConditionToken(lambda: True)], True),
    ([SimpleToken()], False),
    ([ConditionToken(lambda: False)], False),
    ([SimpleToken().cancel()], True),
    ([ConditionToken(lambda: False).cancel()], True),
    ([ConditionToken(lambda: True).cancel()], True),
    ([SimpleToken(), SimpleToken()], False),
    ([SimpleToken(), SimpleToken(), SimpleToken()], False),
    ([SimpleToken(), SimpleToken(), SimpleToken(), SimpleToken()], False),
    ([ConditionToken(lambda: False), ConditionToken(lambda: False)], False),
    ([ConditionToken(lambda: False), ConditionToken(lambda: False), ConditionToken(lambda: False)], False),
])
def test_just_created_condition_token_with_arguments(arguments, expected_cancelled_status):
    assert ConditionToken(lambda: False, *arguments).cancelled == expected_cancelled_status
    assert ConditionToken(lambda: False, *arguments).is_cancelled() == expected_cancelled_status
    assert ConditionToken(lambda: False, *arguments).keep_on() == (not expected_cancelled_status)


def test_raise_without_first_argument():
    with pytest.raises(TypeError):
        ConditionToken()
