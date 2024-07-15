`DefaultToken` is a type of token that cannot be revoked. Otherwise, it behaves like a regular token, but if you try to cancel it, you will get an exception:

```python
DefaultToken().cancel()
#> ...
#> cantok.errors.ImpossibleCancelError: You cannot cancel a default token.
```

It is best to use `DefaultToken` as the default argument for functions:

```python
from cantok import AbstractToken, DefaultToken

def function(token: AbstractToken = DefaultToken):
    ...
```
