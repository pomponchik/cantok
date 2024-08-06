`TimeoutToken` is automatically canceled after the time specified in seconds in the class constructor:

```python
from time import sleep
from cantok import TimeoutToken

token = TimeoutToken(5)
print(token.cancelled)  #> False
sleep(10)
print(token.cancelled)  #> True
```

Just like `ConditionToken`, `TimeoutToken` can include other tokens:

```python
token = TimeoutToken(45, SimpleToken(), TimeoutToken(5), CounterToken(20))  # Includes all additional restrictions of the passed tokens.
```

By default, time is measured using [`perf_counter`](https://docs.python.org/3/library/time.html#time.perf_counter) as the most accurate way to measure time. In extremely rare cases, you may need to use [monotonic](https://docs.python.org/3/library/time.html#time.monotonic_ns)-time, for this use the appropriate initialization argument:

```python
token = TimeoutToken(33, monotonic=True)
```
