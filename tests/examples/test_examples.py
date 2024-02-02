import asyncio
from io import StringIO
from random import randint
from threading import Thread
from contextlib import redirect_stdout

from cantok import SimpleToken, ConditionToken, CounterToken, TimeoutToken


counter = 0

def test_cancel_simple_token_with_function_and_thread():
    def function(token):
        global counter
        while not token.cancelled:
            counter += 1

    token = ConditionToken(lambda: randint(1, 100_000) == 1984) + CounterToken(400_000, direct=False) + TimeoutToken(1)
    thread = Thread(target=function, args=(token, ))
    thread.start()
    thread.join()

    assert counter


def test_cancel_simple_token_with_function_and_thread_2():
    token = ConditionToken(lambda: randint(1, 100_000) == 1984) + CounterToken(400_000, direct=False) + TimeoutToken(1)
    counter = 0

    while token:
      counter += 1

    assert counter


def test_waiting_of_cancelled_token():
    async def do_something(token):
        await asyncio.sleep(0.1)  # Imitation of some real async activity.
        token.cancel()

    async def main():
        token = SimpleToken()
        await do_something(token)
        await token.wait()
        print('Something has been done!')

    buffer = StringIO()
    with redirect_stdout(buffer):
        asyncio.run(main())

    assert buffer.getvalue() == 'Something has been done!\n'


def test_waiting_of_cancelled_token_with_gather():
    async def do_something(token):
        await asyncio.sleep(0.1)  # Imitation of some real async activity.
        token.cancel()

    async def main():
        token = SimpleToken()
        await asyncio.gather(do_something(token), token.wait())
        print('Something has been done!')

    buffer = StringIO()
    with redirect_stdout(buffer):
        asyncio.run(main())

    assert buffer.getvalue() == 'Something has been done!\n'
