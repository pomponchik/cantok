from time import monotonic as current_time
from typing import Union

from ctok.tokens.abstract_token import AbstractToken
from ctok import ConditionToken


class TimeoutToken(ConditionToken):
    def __init__(self, timeout: Union[int, float], *tokens: AbstractToken, cancelled: bool = False):
        if timeout < 0:
            raise ValueError

        start_time = current_time()
        def function() -> bool:
            return (start_time + timeout) < current_time()

        super().__init__(function, *tokens, cancelled=cancelled)
