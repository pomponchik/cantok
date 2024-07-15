To run a function regularly, use [metronomes](https://github.com/pomponchik/metronomes). Just wrap your code in a context manager:

```python
from time import sleep
from metronomes import Metronome

with Metronome(0.2, lambda: print('go!')):
    sleep(1)
#> go!
#> go!
#> go!
#> go!
#> go!
```

You can also manually control the start and stop of the metronome:

```python
metronome = Metronome(0.2, lambda: print('go!'))

metronome.start()
sleep(1)
metronome.stop()
#> go!
#> go!
#> go!
#> go!
#> go!
```

And of course, the cancellation token can be used as an optional argument:

```python
from cantok import TimeoutToken

metronome = Metronome(0.2, lambda: None, token=TimeoutToken(1))

metronome.start()
print(metronome.stopped)
#> False
sleep(1.5)  # Here I specify a little more time than in the constructor of the token itself, since a small margin is needed for operations related to the creation of the metronome object itself.
print(metronome.stopped)
#> True
```
