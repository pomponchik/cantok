`DefaultToken` is a type of token that cannot be revoked. Otherwise, it behaves like a regular token, but if you try to cancel it, you will get an exception:

```python
from cantok import AbstractToken, DefaultToken

DefaultToken().cancel()
#> ...
#> cantok.errors.ImpossibleCancelError: You cannot cancel a default token.
```

In addition, you cannot embed other tokens in `DefaultToken`.

It is best to use `DefaultToken` as the default argument for functions:

```python
def function(token: AbstractToken = DefaultToken()):
    ...
```
