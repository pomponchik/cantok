![logo](https://raw.githubusercontent.com/pomponchik/cantok/main/docs/assets/logo_5.png)

[![Downloads](https://static.pepy.tech/badge/cantok/month)](https://pepy.tech/project/cantok)
[![Downloads](https://static.pepy.tech/badge/cantok)](https://pepy.tech/project/cantok)
[![codecov](https://codecov.io/gh/pomponchik/cantok/graph/badge.svg?token=eZ4eK6fkmx)](https://codecov.io/gh/pomponchik/cantok)
[![Lines of code](https://sloc.xyz/github/pomponchik/cantok/?category=code)](https://github.com/boyter/scc/)
[![Hits-of-Code](https://hitsofcode.com/github/pomponchik/cantok?branch=main)](https://hitsofcode.com/github/pomponchik/cantok/view?branch=main)
[![Test-Package](https://github.com/pomponchik/cantok/actions/workflows/tests_and_coverage.yml/badge.svg)](https://github.com/pomponchik/cantok/actions/workflows/tests_and_coverage.yml)
[![Python versions](https://img.shields.io/pypi/pyversions/cantok.svg)](https://pypi.python.org/pypi/cantok)
[![PyPI version](https://badge.fury.io/py/cantok.svg)](https://badge.fury.io/py/cantok)
[![Checked with mypy](http://www.mypy-lang.org/static/mypy_badge.svg)](http://mypy-lang.org/)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)


Cancellation Token is a pattern that allows us to refuse to continue calculations that we no longer need. It is implemented out of the box in many programming languages, for example in [C#](https://learn.microsoft.com/en-us/dotnet/api/system.threading.cancellationtoken) and in [Go](https://pkg.go.dev/context). However, there was still no sane implementation in Python, until the [cantok](https://github.com/pomponchik/cantok) library appeared.


## Quick start

Install [it](https://pypi.org/project/cantok/):

```bash
pip install cantok
```

And use:

```python
from random import randint
from cantok import ConditionToken, CounterToken, TimeoutToken


token = ConditionToken(lambda: randint(1, 100_000) == 1984) + CounterToken(400_000, direct=False) + TimeoutToken(1)
counter = 0

while token:
  counter += 1

print(counter)
```

Read more in the [documentation](https://cantok.readthedocs.io/en/latest/)!
