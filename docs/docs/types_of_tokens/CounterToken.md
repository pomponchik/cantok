`CounterToken` is the most ambiguous of the tokens presented by this library. Do not use it if you are not sure that you understand how it works correctly. However, it can be very useful in situations where you want to limit the number of attempts to perform an operation.

`CounterToken` is initialized with an integer greater than zero. At each calculation of the answer to the question whether it is canceled, this number is reduced by one. When this number becomes zero, the token is considered canceled:

```python
from cantok import CounterToken

token = CounterToken(5)
counter = 0

while token:
    counter += 1

print(counter)  # 5
```

The counter inside the `CounterToken` is reduced under one of three conditions:

- Access to the `cancelled` attribute.
- Calling the `is_cancelled()` method.
- Calling the `keep_on()` method.

If you use `CounterToken` inside other tokens, the wrapping token can specify the status of the `CounterToken`. For security reasons, this operation does not decrease the counter. However, if for some reason you need it to decrease, pass `direct` - `False` as an argument:

```python
from cantok import SimpleToken, CounterToken

first_counter_token = CounterToken(1, direct=False)
second_counter_token = CounterToken(1, direct=True)

print(SimpleToken(first_counter_token, second_counter_token).cancelled)  # False
print(first_counter_token.cancelled)  # True
print(second_counter_token.cancelled)  # False
```

Like all other tokens, `CounterToken` can accept other tokens as parameters during initialization:

```python
from cantok import SimpleToken, CounterToken, TimeoutToken

token = CounterToken(15, SimpleToken(), TimeoutToken(5))
```
