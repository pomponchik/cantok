from threading import Thread
from random import randint

from cantok import SimpleToken, ConditionToken, CounterToken, TimeoutToken


def test_cancel_simple_token():
    counter = 0

    def function(token):
        nonlocal counter
        while not token.cancelled:
            counter += 1

    token = SimpleToken() + ConditionToken(lambda: randint(1, 1_000_000_000)) + CounterToken(100_000) + TimeoutToken(1)
    thread = Thread(target=function, args=(token, ))
    thread.start()

    thread.join()

    assert counter
