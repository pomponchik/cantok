from time import monotonic_ns, perf_counter

from typing import Union, Callable, Dict, Any

from cantok import AbstractToken
from cantok import ConditionToken
from cantok.errors import TimeoutCancellationError


class TimeoutToken(ConditionToken):
    exception = TimeoutCancellationError

    def __init__(self, timeout: Union[int, float], *tokens: AbstractToken, cancelled: bool = False, monotonic: bool = False):
        if timeout < 0:
            raise ValueError('You cannot specify a timeout less than zero.')

        self.timeout = timeout
        self.monotonic = monotonic

        timer: Callable[[], Union[int, float]]
        if monotonic:
            timeout *= 1_000_000_000
            timer = monotonic_ns
        else:
            timer = perf_counter

        start_time: Union[int, float] = timer()
        def function() -> bool:
            return timer() >= (start_time + timeout)

        super().__init__(function, *tokens, cancelled=cancelled)

    def text_representation_of_superpower(self) -> str:
        return str(self.timeout)

    def get_extra_kwargs(self) -> Dict[str, Any]:
        return {
            'monotonic': self.monotonic,
        }

    def get_superpower_exception_message(self) -> str:
        return f'The timeout of {self.timeout} seconds has expired.'
