from typing import Callable, Dict, Any
from contextlib import suppress

from cantok import AbstractToken
from cantok.errors import ConditionCancellationError


class ConditionToken(AbstractToken):
    exception = ConditionCancellationError

    def __init__(self, function: Callable[[], bool], *tokens: AbstractToken, cancelled: bool = False, suppress_exceptions: bool = True, default: bool = False):
        super().__init__(*tokens, cancelled=cancelled)
        self.function = function
        self.suppress_exceptions = suppress_exceptions
        self.default = default

    def superpower(self) -> bool:
        if not self.suppress_exceptions:
            return self.run_function()

        else:
            with suppress(Exception):
                return self.run_function()

        return self.default

    def run_function(self) -> bool:
        result = self.function()

        if not isinstance(result, bool):
            if not self.suppress_exceptions:
                raise TypeError(f'The condition function can only return a bool value. The passed function returned "{result}" ({type(result).__name__}).')
            else:
                return self.default

        return result

    def text_representation_of_superpower(self) -> str:
        return repr(self.function)

    def get_extra_kwargs(self) -> Dict[str, Any]:
        return {
            'suppress_exceptions': self.suppress_exceptions,
            'default': self.default,
        }

    def get_superpower_exception_message(self) -> str:
        return 'The condition is not met.'
