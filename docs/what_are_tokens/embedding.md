You can embed an unlimited number of other tokens in one token by passing them as arguments during initialization. Each time checking whether it has been cancelled, the token first checks its cancellation rules, and if it has not been cancelled itself, then it checks the tokens nested in it. Thus, one cancelled token nested in another non-cancelled token cancels it:

```python
from cantok import SimpleToken

first_token = SimpleToken()
second_token = SimpleToken()
third_token = SimpleToken(first_token, second_token)

first_token.cancel()

print(first_token.cancelled)  #> True
print(second_token.cancelled)  #> False
print(third_token.cancelled)  #> True
```
