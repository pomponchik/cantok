from contextlib import suppress
from typing import Callable, Dict, Any

from cantok.errors import ConditionCancellationError
from cantok.tokens.abstract.abstract_token import AbstractToken


class ConditionToken(AbstractToken):
    """A token that will be cancelled, when the condition is met.

    ConditionToken has superpower: it can check arbitrary conditions. In addition to this, it can do all the same
    things as SimpleToken. The condition is a function that returns an answer to the question "has the token been
    canceled" (``True``/``False``), it is passed to the token as the first required argument during initialization.

    Example:
        .. code-block:: python

            from cantok import ConditionToken

            counter = 0

            token = ConditionToken(lambda: counter >= 5)

            while token:

                counter += 1

            print(counter)  #> 5


    By default, if the passed function raises an exception, it will be silently suppressed.
    However, you can make the raised exceptions explicit by setting the suppress_exceptions parameter to ``False``.

    Example:
        .. code-block:: python

            def function():

                raise ValueError

            token = ConditionToken(function, suppress_exceptions=False)

            token.cancelled  # ValueError has risen.


    If you still use exception suppression mode, by default, in case of an exception, the canceled attribute
    will contain ``False``. If you want to change this, pass it there as the default parameter - ``True``.

    Example:
        .. code-block:: python

            def function():

                raise ValueError

            print(ConditionToken(function).cancelled)  # False

            print(ConditionToken(function, default=False).cancelled)  # False

            print(ConditionToken(function, default=True).cancelled)  # True

    If the condition is complex enough and requires additional preparation before it can be checked, you can pass
    a function that runs before the condition is checked. To do this, pass any function without arguments as the
    ``before`` argument.

    Example:
        .. code-block:: python

            from cantok import ConditionToken

            token = ConditionToken(lambda: print(2), before=lambda: print(1))

            token.check()

            #> 1

            #> 2

    By analogy with ``before``, you can pass a function that will be executed after checking the condition
    as the ``after`` argument.

    Example:
        .. code-block:: python

            token = ConditionToken(lambda: print(1), after=lambda: print(2))

            token.check()

            #> 1

            #> 2

    ConditionToken has another feature. If the condition has detonated at least once and canceled it,
    then the condition is no longer polled and the token is permanently considered canceled.
    You can change this by manipulating the caching parameter when creating a token. By setting it to ``False``,
    you will make sure that the condition is polled every time.

    Example:
        .. code-block:: python

            counter = 0

            def increment_counter_and_get_the_value():

                global counter

                counter += 1

                return counter == 2


            token = ConditionToken(increment_counter_and_get_the_value, caching=False)

            print(token.cancelled)  # False

            print(token.cancelled)  # True

            print(token.cancelled)  # False

    However, doing this is not recommended. In the vast majority of cases, you do not want your token
    to be able to roll back the fact of its cancellation. If the token has been cancelled once, it must
    remain cancelled. Manipulate the caching parameter only if you are sure that you understand what you are doing.

    :type: AbstractToken
    :param function: any function that returns True or False
    :param tokens: iterable of tokens
    :param cancelled: boolean flag indicating whether this token is cancelled, by default ``False``
    :param suppress_exceptions: boolean flag indicating whether exceptions should be suppressed, by default ``True``
    :param default: ????
    :param before: ????
    :param after: ????
    :param caching: boolean flag indicating whether to use caching or not, by default ``True`` ?????????
    """

    # TODO: лучше protected
    exception = ConditionCancellationError

    def __init__(
            self,
            function: Callable[[], bool],
            *tokens: AbstractToken,
            cancelled: bool = False,
            suppress_exceptions: bool = True,
            default: bool = False,
            before: Callable[[], Any] = lambda: None,
            after: Callable[[], Any] = lambda: None,
            caching: bool = True
    ):
        super().__init__(*tokens, cancelled=cancelled)

        self.function = function
        self.before = before
        self.after = after
        self.suppress_exceptions = suppress_exceptions
        self.default = default
        self.caching = caching
        self.was_cancelled_by_condition = False

    # TODO: видимо в protected
    def superpower(self) -> bool:
        if self.was_cancelled_by_condition and self.caching:
            return True

        if not self.suppress_exceptions:
            self.before()
            result = self.run_function()
            self.after()
            return result

        else:
            result = self.default

            with suppress(Exception):
                self.before()
            with suppress(Exception):
                result = self.run_function()
            with suppress(Exception):
                self.after()

            return result

    # TODO: видимо в protected
    def run_function(self) -> bool:
        result = self.function()

        if not isinstance(result, bool):
            if not self.suppress_exceptions:
                raise TypeError(
                    f'The condition function can only return a bool value. The passed function returned "{result}" ({type(result).__name__}).')
            else:
                return self.default

        else:
            if result:
                self.was_cancelled_by_condition = True

        return result

    # TODO: видимо в protected
    def text_representation_of_superpower(self) -> str:
        if hasattr(self.function, '__name__'):
            result = self.function.__name__

            if result == '<lambda>':
                return 'λ'

            return result

        else:
            return repr(self.function)

    # TODO: видимо в protected
    def get_extra_kwargs(self) -> Dict[str, Any]:
        result = {}

        if not self.suppress_exceptions:
            result['suppress_exceptions'] = self.suppress_exceptions

        if self.default is not False:
            result['default'] = self.default  # type: ignore[assignment]

        return result

    # TODO: видимо в protected
    def get_superpower_exception_message(self) -> str:
        return 'The cancellation condition was satisfied.'
