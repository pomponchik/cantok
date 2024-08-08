from time import monotonic_ns, perf_counter
from typing import Union, Callable, List, Dict, Any

from cantok import AbstractToken
from cantok import ConditionToken
from cantok.errors import TimeoutCancellationError
from cantok.types import IterableWithTokens


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
        deadline = start_time + timeout
        def function() -> bool:
            return timer() >= deadline

        self.deadline = deadline

        super().__init__(function, *tokens, cancelled=cancelled)

    def filter_tokens(self, tokens: IterableWithTokens) -> List[AbstractToken]:  # type: ignore[type-arg]
        result: List[AbstractToken] = []

        for token in tokens:
            if isinstance(token, TimeoutToken) and token.monotonic == self.monotonic and self.deadline <= token.deadline:
                result.extend(token.tokens)
            else:
                result.append(token)

        return super().filter_tokens(result)

    def text_representation_of_superpower(self) -> str:
        return str(self.timeout)

    def get_extra_kwargs(self) -> Dict[str, Any]:
        if self.monotonic:
            return {
                'monotonic': self.monotonic,
            }
        return {}

    def get_superpower_exception_message(self) -> str:
        return f'The timeout of {self.timeout} seconds has expired.'
