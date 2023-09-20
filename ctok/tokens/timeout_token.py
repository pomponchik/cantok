from time import monotonic_ns, perf_counter

from typing import Union

from ctok.tokens.abstract_token import AbstractToken
from ctok import ConditionToken


class TimeoutToken(ConditionToken):
    def __init__(self, timeout: Union[int, float], *tokens: AbstractToken, cancelled: bool = False, monotonic: bool = True):
        if timeout < 0:
            raise ValueError

        if monotonic:
            timeout *= 1_000_000_000

            start_time = monotonic_ns()
            def function() -> bool:
                return monotonic_ns() >= (start_time + timeout)

        else:
            start_time = perf_counter()
            def function() -> bool:
                return perf_counter() >= (start_time + timeout)

        super().__init__(function, *tokens, cancelled=cancelled)
