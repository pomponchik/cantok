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
from time import sleep
from threading import Thread
from cantok import SimpleToken


counter = 0

def function(token):
    nonlocal counter
    while not token.cancelled:
        counter += 1

token = SimpleToken()
thread = Thread(target=function, args=(token, ))
thread.start()

sleep(1)

token.cancel()
thread.join()

assert counter
```

## The pattern


## Tokens


### Simple token
### Condition token
### Timeout token
### Counter token
