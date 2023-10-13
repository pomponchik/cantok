Consider an example:

```python
from random import randint
from cantok import ConditionToken, CounterToken, TimeoutToken


token = ConditionToken(lambda: randint(1, 100_000) == 1984) + CounterToken(400_000, direct=False) + TimeoutToken(1)
counter = 0

while token:
  counter += 1

print(counter)
```

In this code, we use a token that describes several restrictions: on the [number of iterations](/types_of_tokens/CounterToken/) of the cycle, on [time](/types_of_tokens/TimeoutToken/), as well as on the [occurrence](/types_of_tokens/ConditionToken/) of a random unlikely event. When any of the indicated events occur, the cycle stops.

In fact, the library's capabilities are much broader, read the documentation below.
