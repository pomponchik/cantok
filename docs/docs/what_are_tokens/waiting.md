Each token has an async method, `wait()`, which transfers control until the token is canceled. It can be passed to one or more asynchronous functions, then wait until they cancel the operation, and then continue further work, something like this:

```python
import asyncio
from cantok import SimpleToken

async def do_something(token):
  await asyncio.sleep(3)  # Imitation of some real async activity.
  token.cancel()

async def main():
  token = SimpleToken()
  await do_something(token)
  await token.wait()
  print('Something has been done!')

asyncio.run(main())
```

The `wait()` method has two optional arguments:

- **`timeout`** (`int` or `float`) - the maximum waiting time in seconds. If this time is exceeded, a [`TimeoutCancellationError` exception](/what_are_tokens/waiting/) will be raised. By default, the `timeout` is not set.
- **`step`** (`int` or `float`, by default `0.0001`) - the duration of the iteration, once in which the token state is polled, in seconds. For obvious reasons, you cannot set this value to a number that exceeds the `timeout`.
