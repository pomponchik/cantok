A token is an object that can tell you whether to continue the action you started, or whether it has already been canceled.

There are 4 types of tokens in this library:

- [`SimpleToken`](../types_of_tokens/SimpleToken.md)
- [`ConditionToken`](../types_of_tokens/ConditionToken.md)
- [`TimeoutToken`](../types_of_tokens/TimeoutToken.md)
- [`CounterToken`](../types_of_tokens/CounterToken.md)

Each of them has its own characteristics, but they also have something in common:

- Each token can be canceled manually, and some types of tokens can cancel themselves when a condition or timeout occurs. It doesn't matter how the token was canceled, you work with it the same way.

- All types of tokens are thread-safe and can be used from multiple threads/coroutines. However, they are not intended to be shared from multiple processes.

- Token cancellation is a one-way operation. A token that has already been cancelled cannot be restored.

- All token classes are inherited from `AbstractToken` and have a single interface that defines how they can be canceled, how to find out their status, how to expect their cancellation and much more. If you are writing a function that accepts an unknown token type, you can use `AbstractToken` to hint types:

```python
from cantok import AbstractToken

def function(token: AbstractToken):
  ...
```
