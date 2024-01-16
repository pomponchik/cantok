ConditionToken has superpower, it can check arbitrary conditions. In addition to this, it can do all the same things as [`SimpleToken`](/types_of_tokens/SimpleToken/). The condition must be passed to the token constructor as the first argument. The condition is a function that should return an answer (`True`/`False`) to the question "has the token been canceled?", it must be passed to the token constructor with the first argument:

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

If the condition is complex enough and requires additional preparation before it can be checked, you can pass a function that runs before the condition is checked. To do this, pass any function without arguments as the `before` argument:

```python
from cantok import ConditionToken

token = ConditionToken(lambda: print(2), before=lambda: print(1))

token.check()
# Will be printed:
# 1
# 2
```
