Any tokens can be summed up among themselves. The summation operation generates another [`SimpleToken`](#simple-token) that includes the previous 2:

```python
from cantok import SimpleToken, TimeoutToken

print(repr(SimpleToken() + TimeoutToken(5)))
# SimpleToken(SimpleToken(), TimeoutToken(5, monotonic=False))
```

This feature is convenient to use if your function has received a token with certain restrictions and wants to throw it into other called functions, imposing additional restrictions:

```python
from cantok import AbstractToken, TimeoutToken

def function(token: AbstractToken):
  ...
  another_function(token + TimeoutToken(5))  # Imposes an additional restriction on the function being called: work for no more than 5 seconds. At the same time, it does not know anything about what restrictions were imposed earlier.
  ...
```
