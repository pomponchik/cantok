Each token class has its own exception and it can be found in the `exception` attribute of the class:

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
