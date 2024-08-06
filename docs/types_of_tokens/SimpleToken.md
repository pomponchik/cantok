The base token is `SimpleToken`. It has no built-in automation that can cancel it. The only way to cancel `SimpleToken` is to explicitly call the `cancel()` method from it.

```python
from cantok import SimpleToken

token = SimpleToken()
print(token.cancelled)  #> False
token.cancel()
print(token.cancelled)  #> True
```

There is not much more to tell about it if you have read [the story](../what_are_tokens/in_general.md) about tokens in general.
