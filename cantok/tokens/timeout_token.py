from time import monotonic_ns, perf_counter
from typing import Any, Callable, Dict, Union

from cantok import AbstractToken, ConditionToken
from cantok.errors import TimeoutCancellationError


class TimeoutToken(ConditionToken):
    exception = TimeoutCancellationError

    def __init__(self, timeout: Union[int, float], *tokens: AbstractToken, cancelled: bool = False, monotonic: bool = False):
        if timeout < 0:
            raise ValueError('You cannot specify a timeout less than zero.')

        self._timeout = timeout
        self._monotonic = monotonic

        timer: Callable[[], Union[int, float]]
        if monotonic:
            timeout *= 1_000_000_000
            timer = monotonic_ns
        else:
            timer = perf_counter

        start_time: Union[int, float] = timer()
        deadline = start_time + timeout
        def function() -> bool:
            return timer() >= deadline

        self._deadline = deadline

        super().__init__(function, *tokens, cancelled=cancelled)

    def _text_representation_of_superpower(self) -> str:
        return str(self._timeout)

    def _get_extra_kwargs(self) -> Dict[str, Any]:
        if self._monotonic:
            return {
                'monotonic': self._monotonic,
            }
        return {}

    def _get_superpower_exception_message(self) -> str:
        return f'The timeout of {self._timeout} seconds has expired.'
