from time import monotonic_ns as current_time

from typing import Union

from ctok.tokens.abstract_token import AbstractToken
from ctok import ConditionToken


class TimeoutToken(ConditionToken):
    def __init__(self, timeout: Union[int, float], *tokens: AbstractToken, cancelled: bool = False):
        if timeout < 0:
            raise ValueError

        timeout *= 1_000_000_000

        start_time = current_time()
        def function() -> bool:
            return current_time() >= (start_time + timeout)

        super().__init__(function, *tokens, cancelled=cancelled)
