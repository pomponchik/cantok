Tokens can be summed using the operator `+`:

```python
first_token = TimeoutToken(5)
second_token = ConditionToken(lambda: True)
print(repr(first_token + second_token))
#> SimpleToken(TimeoutToken(5), ConditionToken(λ))
```

This feature is convenient to use if your function has received a token with certain restrictions and wants to throw it into other called functions, imposing additional restrictions:

```python
from cantok import AbstractToken, TimeoutToken

def function(token: AbstractToken):
  ...
  another_function(token + TimeoutToken(5))  # Imposes an additional restriction on the function being called: work for no more than 5 seconds. At the same time, it does not know anything about what restrictions were imposed earlier.
  ...
```

The token summation operation always generates a new token. If at least one of the operand tokens is canceled, the sum will also be canceled. It is also guaranteed that the cancellation of this token does not lead to the cancellation of operands. That is, the sum of two tokens always behaves as if it were a [`SimpleToken`](../types_of_tokens/SimpleToken.md) in which both operands were [nested](embedding.md). However, it is difficult to say exactly which token will result from summation, since the library strives to minimize the generated graph of tokens for the sake of performance.

You may notice that some tokens disappear altogether during summation:

```python
print(repr(SimpleToken() + TimeoutToken(5)))
#> TimeoutToken(5)
print(repr(SimpleToken(cancelled=True) + TimeoutToken(5)))
#> SimpleToken(cancelled=True)
```

In addition, you can not be afraid to sum more than 2 tokens - this does not generate anything superfluous:

```python
print(repr(TimeoutToken(5) + ConditionToken(lambda: False) + CounterToken(23)))
#> TimeoutToken(5, ConditionToken(λ), CounterToken(23))
```

In fact, there are quite a few effective ways to optimize the token addition operation that are implemented in the library. This operation is pretty well optimized, so it is recommended in all cases when you need to combine the constraints of different tokens in one.
