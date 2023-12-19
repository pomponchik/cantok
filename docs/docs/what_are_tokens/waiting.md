Each token has `wait()` method, which allows you to wait for its cancellation.

```python
from cantok import TimeoutToken

token = TimeoutToken(5)
token.wait()  # It will take about 5 seconds.
token.check()  # Since the timeout has expired, an exception will be raised.
# cantok.errors.TimeoutCancellationError: The timeout of 5 seconds has expired.
```

This method also has an async version. To make the wait asynchronous, simply add the `is_async=True` parameter. After that, you can use this method in expressions using the `await` statement:

```python
import asyncio
from cantok import SimpleToken

async def do_something(token):
  await asyncio.sleep(3)  # Imitation of some real async activity.
  token.cancel()

async def main():
  token = SimpleToken()
  await do_something(token)
  await token.wait(is_async=True)
  print('Something has been done!')

asyncio.run(main())
```

If you mistakenly use the `await` statement in the synchronous mode of the method, you will receive a `cantok.errors.SynchronousWaitingError`:

```python
await token.wait()
#  cantok.errors.SynchronousWaitingError: You cannot use the "await" keyword in the synchronous mode of the method. Add the "is_async" (bool) argument.
```

In addition to the above, the `wait()` method has two optional arguments:

- **`timeout`** (`int` or `float`) - the maximum waiting time in seconds. If this time is exceeded, a [`TimeoutCancellationError` exception](/what_are_tokens/waiting/) will be raised. By default, the `timeout` is not set.
- **`step`** (`int` or `float`, by default `0.0001`) - the duration of the iteration, once in which the token state is polled, in seconds. For obvious reasons, you cannot set this value to a number that exceeds the `timeout`.
