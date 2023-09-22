from threading import Thread
from random import randint

from cantok import ConditionToken, CounterToken, TimeoutToken


counter = 0

def test_cancel_simple_token():
    def function(token):
        global counter
        while not token.cancelled:
            counter += 1

    token = ConditionToken(lambda: randint(1, 100_000) == 1984) + CounterToken(400_000, direct=False) + TimeoutToken(1)
    thread = Thread(target=function, args=(token, ))
    thread.start()
    thread.join()

    assert counter
