![logo](https://raw.githubusercontent.com/pomponchik/cantok/develop/docs/assets/logo_2.png)

[![Downloads](https://static.pepy.tech/badge/cantok/month)](https://pepy.tech/project/cantok)
[![Downloads](https://static.pepy.tech/badge/cantok)](https://pepy.tech/project/cantok)
[![codecov](https://codecov.io/gh/pomponchik/cantok/graph/badge.svg?token=eZ4eK6fkmx)](https://codecov.io/gh/pomponchik/cantok)
[![Test-Package](https://github.com/pomponchik/cantok/actions/workflows/tests_and_coverage.yml/badge.svg)](https://github.com/pomponchik/cantok/actions/workflows/tests_and_coverage.yml)
[![Python versions](https://img.shields.io/pypi/pyversions/cantok.svg)](https://pypi.python.org/pypi/cantok)
[![PyPI version](https://badge.fury.io/py/cantok.svg)](https://badge.fury.io/py/cantok)
[![Checked with mypy](http://www.mypy-lang.org/static/mypy_badge.svg)](http://mypy-lang.org/)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)


Cancellation Token is a pattern that allows us to refuse to continue calculations that we no longer need. It is implemented out of the box in many programming languages, for example in [C#](https://learn.microsoft.com/en-us/dotnet/api/system.threading.cancellationtoken) and in [Go](https://pkg.go.dev/context). However, there was still no sane implementation in Python, until the [cantok](https://github.com/pomponchik/cantok) library appeared.


## Table of contents

- [**Quick start**](#quick-start)
- [**The pattern**](#the-pattern)
- [**Tokens**](#tokens)
  - [**Simple token**](#simple-token)
  - [**Condition token**](#simple-token)
  - [**Timeout token**](#timeout-token)
  - [**Counter token**](#counter-token)


## Quick start

Install [it](https://pypi.org/project/cantok/):

```bash
pip install cantok
```

And use:

```python
from random import randint
from threading import Thread

from cantok import ConditionToken, CounterToken, TimeoutToken


counter = 0

def function(token):
    global counter
    while not token.cancelled:
        counter += 1

token = ConditionToken(lambda: randint(1, 100_000) == 1984) + CounterToken(400_000, direct=False) + TimeoutToken(1)
thread = Thread(target=function, args=(token, ))
thread.start()
thread.join()

print(counter)
```

In this example, we pass a token to the function that describes several restrictions: on the [number of iterations](#counter-token) of the cycle, on [time](#timeout-token), as well as on the [occurrence](#condition-token) of a random unlikely event. When any of the indicated events occur, the cycle stops.

Read more about the [possibilities of tokens](#tokens), as well as about the [pattern in general](#the-pattern).


## The pattern

The essence of the pattern is that we pass special objects to functions and constructors, by which the executed code can understand whether it should continue its execution or not. When deciding whether to allow code execution to continue, this object can take into account both the restrictions specified to it, such as the maximum code execution time, and receive signals about the need to stop from the outside, for example from another thread or a coroutine. Thus, we do not nail down the logic associated with stopping code execution, for example, by directly tracking cycle counters, but implement [Dependency Injection](https://en.wikipedia.org/wiki/Dependency_injection) of this restriction.

In addition, the pattern assumes that various restrictions can be combined indefinitely with each other: if at least one of the restrictions is not met, code execution will be interrupted. It is assumed that each function in the call stack will call other functions, throwing its token directly to them, or wrapping it in another token, with a stricter restriction imposed on it.

Unlike other ways of interrupting code execution, tokens do not force the execution thread to be interrupted forcibly. The interruption occurs "gently", allowing the code to terminate correctly, return all occupied resources and restore consistency.

It is highly desirable for library developers to use this pattern for any long-term composite operations. Your function can accept a token as an optional argument, with a default value that imposes minimal restrictions or none at all. If the user wishes, he can transfer his token there, imposing stricter restrictions on the library code. In addition to a more convenient and extensible API, this will give the library an advantage in the form of better testability, because the restrictions are no longer sewn directly into the function, which means they can be made whatever you want for the test. In addition, the library developer no longer needs to think about all the numerous restrictions that can be imposed on his code - the user can take care of it himself if he needs to.


## Tokens

All token classes presented in this library have a uniform interface. And they are all inherited from one class: `AbstractToken`. The only reason why you might want to import it is to use it for a type hint. This example illustrates a type hint suitable for any of the tokens:

```python
from cantok import AbstractToken

def function(token: AbstractToken):
  ...
```

Each token object has a `cancelled` attribute and a `cancel()` method. By the attribute, you can find out whether this token has been canceled:

```python
from cantok import SimpleToken

token = SimpleToken()
print(token.cancelled)  # False
token.cancel()
print(token.cancelled)  # True
```

The cancelled attribute is dynamically calculated and takes into account, among other things, specific conditions that are checked by a specific token. Here is an example with a [token that measures time](#timeout-token):

```python
from time import sleep
from cantok import TimeoutToken

token = TimeoutToken(5)
print(token.cancelled)  # False
sleep(10)
print(token.cancelled)  # True
```

In addition to this attribute, each token implements the `is_cancelled()` method. It does exactly the same thing as the attribute:

```python
from cantok import SimpleToken

token = SimpleToken()
print(token.cancelled)  # False
print(token.is_cancelled())  # False
token.cancel()
print(token.cancelled)  # True
print(token.is_cancelled())  # True
```

Choose what you like best. To the author of the library, the use of the attribute seems more beautiful, but the method call more clearly reflects the complexity of the work that is actually being done to answer the question "has the token been canceled?".

There is another method opposite to `is_cancelled()` - `keep_on()`. It answers the opposite question, and can be used in the same situations:

```python
from cantok import SimpleToken

token = SimpleToken()
print(token.cancelled)  # False
print(token.keep_on())  # True
token.cancel()
print(token.cancelled)  # True
print(token.keep_on())  # False
```

An unlimited number of other tokens can be embedded in one token as arguments during initialization. Each time checking whether it has been canceled, the token first checks its cancellation rules, and if it has not been canceled itself, then it checks the tokens nested in it. Thus, one cancelled token nested in another non-cancelled token cancels it:

```python
from cantok import SimpleToken

first_token = SimpleToken()
second_token = SimpleToken()
third_token = SimpleToken(first_token, second_token)

first_token.cancel()

print(first_token.cancelled)  # True
print(second_token.cancelled)  # False
print(third_token.cancelled)  # True
```

### Simple token
### Condition token
### Timeout token
### Counter token
