To work with subprocesses, there is a [`suby`](https://github.com/pomponchik/suby) library with support for cancellation tokens. It has a very simple syntax:

```python
import suby

suby('python', '-c', 'print("hello, world!")')
```

A token can be passed as an argument:

```python
suby('python', '-c', 'import time; time.sleep(10_000)', token=TimeoutToken(1), catch_exceptions=True)
```
