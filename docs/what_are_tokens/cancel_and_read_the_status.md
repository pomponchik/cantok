Each token object has a `cancelled` attribute and a `cancel()` method. By the attribute, you can find out whether this token has been canceled:

```python
from cantok import SimpleToken

token = SimpleToken()
print(token.cancelled)  # False
token.cancel()
print(token.cancelled)  # True
```

The cancelled attribute is dynamically calculated and takes into account, among other things, specific conditions that are checked by a specific token. Here is an example with a [token that measures time](types_of_tokens/TimeoutToken.md):

```python
from time import sleep
from cantok import TimeoutToken

token = TimeoutToken(5)
print(token.cancelled)  # False
sleep(10)
print(token.cancelled)  # True
```

In addition to this attribute, each token implements the `is_cancelled()` method. It does exactly the same thing as the attribute:

```python
from cantok import SimpleToken

token = SimpleToken()
print(token.cancelled)  # False
print(token.is_cancelled())  # False
token.cancel()
print(token.cancelled)  # True
print(token.is_cancelled())  # True
```

Choose what you like best. To the author of the library, the use of the attribute seems more beautiful, but the method call more clearly reflects the complexity of the work that is actually being done to answer the question "has the token been canceled?".

There is another method opposite to `is_cancelled()` - `keep_on()`. It answers the opposite question, and can be used in the same situations:

```python
from cantok import SimpleToken

token = SimpleToken()
print(token.cancelled)  # False
print(token.keep_on())  # True
token.cancel()
print(token.cancelled)  # True
print(token.keep_on())  # False
```

You don't have to call the `keep_on()` method directly. Use the token itself as a boolean value, and the method call will occur "under the hood" automatically:

```python
from cantok import SimpleToken

token = SimpleToken()
print(bool(token))  # True
print(token.keep_on())  # True
token.cancel()
print(bool(token))  # False
print(token.keep_on())  # False
```

There is another method that is close in meaning to `is_cancelled()` - `check()`. It does nothing if the token is not canceled, or raises an exception if canceled. If the token was canceled by calling the `cancel()` method, a `CancellationError` exception will be raised:

```python
from cantok import SimpleToken

token = SimpleToken()
token.check()  # Nothing happens.
token.cancel()
token.check()  # cantok.errors.CancellationError: The token has been cancelled.
```

Otherwise, a special exception inherited from `CancellationError` will be raised:

```python
from cantok import TimeoutToken

token = TimeoutToken(0)
token.check()  # cantok.errors.TimeoutCancellationError: The timeout of 0 seconds has expired.
```
