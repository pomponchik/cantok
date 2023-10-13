All token classes presented in this library have a uniform interface. All tokens are thread-safe. And they are all inherited from one class: `AbstractToken`. The only reason why you might want to import it is to use it for a type hint. This example illustrates a type hint suitable for any of the tokens:

```python
from cantok import AbstractToken

def function(token: AbstractToken):
  ...
```
