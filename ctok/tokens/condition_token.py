from typing import Callable
from contextlib import suppress

from ctok.tokens.abstract_token import AbstractToken


class ConditionToken(AbstractToken):
    def __init__(self, function: Callable[[], bool], *tokens: AbstractToken, suppress_exceptions: bool = True, cancelled: bool = False):
        super().__init__(*tokens, cancelled=cancelled)
        self.function = function
        self.suppress_exceptions = suppress_exceptions

    def superpower(self) -> bool:
        if not self.suppress_exceptions:
            return self.function()

        else:
            with suppress(Exception):
                return self.function()

        return False
