from time import monotonic_ns, perf_counter
from typing import Union, Callable, Dict, Any

from cantok.errors import TimeoutCancellationError
from cantok.tokens import ConditionToken
from cantok.tokens.abstract.abstract_token import AbstractToken


class TimeoutToken(ConditionToken):
    """TimeoutToken is automatically canceled after the time specified in seconds in the class constructor.

    Example:
        .. code-block:: python

            from time import sleep

            from cantok import TimeoutToken

            token = TimeoutToken(5)

            print(token.cancelled)  #> False

            sleep(10)

            print(token.cancelled)  #> True

    Just like ConditionToken, TimeoutToken can include other tokens:

    Example:
        .. code-block:: python

            # Includes all additional restrictions of the passed tokens.

            token = TimeoutToken(45, SimpleToken(), TimeoutToken(5), CounterToken(20))

    By default, time is measured using ``perf_counter`` as the most accurate way to measure time. In extremely
    rare cases, you may need to use monotonic-time, for this use the appropriate initialization argument

    Example:
        .. code-block:: python

            token = TimeoutToken(33, monotonic=True)

    :type: ConditionToken
    :param timeout: Timeout in seconds (may be float).
    :param tokens: iterable of tokens
    :param cancelled: boolean flag indicating whether this token is cancelled, by default ``False``
    :param monotonic: boolean flag indicating whether this to use is ``time.monotonic`` instead of
        ``time.perf_counter``, by default ``False``
    """

    # TODO: лучше protected
    exception = TimeoutCancellationError

    def __init__(
            self,
            timeout: Union[int, float],
            *tokens: AbstractToken,
            cancelled: bool = False,
            monotonic: bool = False
    ):
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
        deadline = start_time + timeout

        def function() -> bool:
            return timer() >= deadline

        self.deadline = deadline

        super().__init__(function, *tokens, cancelled=cancelled)

    # TODO: лучше protected
    def text_representation_of_superpower(self) -> str:
        return str(self.timeout)

    # TODO: лучше protected
    def get_extra_kwargs(self) -> Dict[str, Any]:
        if self.monotonic:
            return {
                'monotonic': self.monotonic,
            }
        return {}

    # TODO: лучше protected
    def get_superpower_exception_message(self) -> str:
        return f'The timeout of {self.timeout} seconds has expired.'
