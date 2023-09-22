from time import sleep
from queue import Queue
from threading import Thread

from cantok import SimpleToken


def test_cancel_simple_token():
    counter = 0

    def function(token):
        nonlocal counter
        while not token.cancelled:
            counter += 1

    token = SimpleToken()
    thread = Thread(target=function, args=(token, ))
    thread.start()

    sleep(1)

    token.cancel()
    thread.join()

    assert counter
