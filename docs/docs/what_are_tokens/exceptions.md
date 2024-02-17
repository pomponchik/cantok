When a token is canceled, you can call the `check()` method from it and an exception will be raised:

```python
from cantok import TimeoutToken

token = TimeoutToken(1)
token.wait()
token.check()
# cantok.errors.TimeoutCancellationError: The timeout of 1 seconds has expired.
```

Each type of token has a corresponding type of exception that can be raised in this case:

```
SimpleToken -> CancellationError
ConditionToken -> ConditionCancellationError
TimeoutToken -> TimeoutCancellationError
CounterToken -> CounterCancellationError
```

When you call the `check()` method on any token, one of two things will happen. If it (or any of the tokens nested in it) was canceled by calling the `cancel()` method, `CancellationError` will always be raised. But if the cancellation occurred as a result of the unique ability of the token, such as for `TimeoutToken` - timeout expiration, then an exception specific to this type of token will be raised.

You can import each of these exceptions from the library directly:

```python
from cantok import CancellationError, ConditionCancellationError, TimeoutCancellationError, CounterCancellationError
```

Also each token class has its own exception and it can be found in the `exception` attribute of the class:

```python
from cantok import TimeoutToken, CancellationError

token = TimeoutToken(0)

try:
    token.check()
except CancellationError as e:
    print(type(e) is TimeoutToken.exception)  # True
```

Each exception object has a `token` attribute indicating the specific token that was canceled. This can be useful in situations where several tokens are nested in one another and you want to find out which one has been canceled:

```python
from cantok import SimpleToken, TimeoutToken, CancellationError

nested_token = TimeoutToken(0)
token = SimpleToken(nested_token)

try:
    token.check()
except CancellationError as e:
    print(e.token is nested_token)  # True
```
