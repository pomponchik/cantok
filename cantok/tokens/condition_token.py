from contextlib import suppress
from typing import Any, Callable, Dict

from cantok import AbstractToken
from cantok.errors import ConditionCancellationError


class ConditionToken(AbstractToken):
    exception = ConditionCancellationError

    def __init__(self, function: Callable[[], bool], *tokens: AbstractToken, cancelled: bool = False, suppress_exceptions: bool = True, default: bool = False, before: Callable[[], Any] = lambda: None, after: Callable[[], Any] = lambda: None, caching: bool = True):  # noqa: PLR0913
        super().__init__(*tokens, cancelled=cancelled)

        self.function = function
        self.before = before
        self.after = after
        self.suppress_exceptions = suppress_exceptions
        self.default = default
        self.caching = caching
        self.was_cancelled_by_condition = False

    def _superpower(self) -> bool:
        if self.was_cancelled_by_condition and self.caching:
            return True

        if not self.suppress_exceptions:
            self.before()
            result = self.run_function()
            self.after()
            return result

        result = self.default

        with suppress(Exception):
            self.before()
        with suppress(Exception):
            result = self.run_function()
        with suppress(Exception):
            self.after()

        return result

    def run_function(self) -> bool:
        result = self.function()

        if not isinstance(result, bool):
            if not self.suppress_exceptions:
                raise TypeError(f'The condition function can only return a bool value. The passed function returned "{result}" ({type(result).__name__}).')
            return self.default

        if result:
            self.was_cancelled_by_condition = True

        return result

    def _text_representation_of_superpower(self) -> str:
        if hasattr(self.function, '__name__'):
            result = self.function.__name__

            if result == '<lambda>':
                return 'λ'

            return result

        return repr(self.function)

    def _get_extra_kwargs(self) -> Dict[str, Any]:
        result = {}

        if not self.suppress_exceptions:
            result['suppress_exceptions'] = self.suppress_exceptions

        if self.default is not False:
            result['default'] = self.default  # type: ignore[assignment]

        return result

    def get_superpower_exception_message(self) -> str:
        return 'The cancellation condition was satisfied.'
