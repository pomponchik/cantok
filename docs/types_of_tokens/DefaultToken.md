`DefaultToken` is a type of token that cannot be cancelled — if you try to cancel it, an exception will be raised:

```python
from cantok import AbstractToken, DefaultToken

DefaultToken().cancel()
#> ...
#> cantok.errors.ImpossibleCancelError: You cannot cancel a default token.
```

In addition, you cannot embed other tokens in `DefaultToken`. In all other respects, it behaves like a regular token.

It is best to use `DefaultToken` as the default argument for functions:

```python
def function(token: AbstractToken = DefaultToken()):
    ...
```
