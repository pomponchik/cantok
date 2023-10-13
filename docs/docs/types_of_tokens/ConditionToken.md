A slightly more complex type of token than [`SimpleToken`](/types_of_tokens/SimpleToken/) is `ConditionToken`. In addition to everything that `SimpleToken` does, it also checks the condition passed to it as a first argument, answering the question whether it has been canceled.

To initialize `ConditionToken`, pass a function to it that does not accept arguments and returns a boolean value. If it returns `True`, it means that the operation has been canceled:

```python
from cantok import ConditionToken

counter = 0
token = ConditionToken(lambda: counter >= 5)

while token:
  counter += 1

print(counter)  # 5
```

By default, if the passed function raises an exception, it will be silently suppressed. However, you can make the raised exceptions explicit by setting the `suppress_exceptions` parameter to `False`:

```python
def function(): raise ValueError

token = ConditionToken(function, suppress_exceptions=False)

token.cancelled #  ValueError has risen.
```

If you still use exception suppression mode, by default, in case of an exception, the `canceled` attribute will contain `False`. If you want to change this, pass it there as the `default` parameter - `True`.

```python
def function(): raise ValueError

print(ConditionToken(function).cancelled)  # False
print(ConditionToken(function, default=False).cancelled)  # False
print(ConditionToken(function, default=True).cancelled)  # True
```

`ConditionToken` may include other tokens during initialization:

```python
token = ConditionToken(lambda: False, SimpleToken(), TimeoutToken(5), CounterToken(20))  # Includes all additional restrictions of the passed tokens.
```
