`ConditionToken has superpower`: it can check arbitrary conditions. In addition to this, it can do all the same things as [`SimpleToken`](/types_of_tokens/SimpleToken/). The condition is a function that returns an answer to the question "has the token been canceled" (`True`/`False`), it is passed to the token as the first required argument during initialization:

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

By analogy with `before`, you can pass a function that will be executed after checking the condition as the `after` argument:

```python
from cantok import ConditionToken

token = ConditionToken(lambda: print(1), after=lambda: print(2))

token.check()
# Will be printed:
# 1
# 2
```
