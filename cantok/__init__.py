from cantok.tokens.abstract_token import AbstractToken as AbstractToken  # noqa: F401
from cantok.tokens.simple_token import SimpleToken as SimpleToken  # noqa: F401
from cantok.tokens.condition_token import ConditionToken as ConditionToken  # noqa: F401
from cantok.tokens.counter_token import CounterToken as CounterToken  # noqa: F401
from cantok.tokens.default_token import DefaultToken as DefaultToken  # noqa: F401
from cantok.tokens.timeout_token import TimeoutToken as TimeoutToken

from cantok.errors import CancellationError as CancellationError, ConditionCancellationError as ConditionCancellationError, CounterCancellationError as CounterCancellationError, TimeoutCancellationError as TimeoutCancellationError, ImpossibleError as ImpossibleError  # noqa: F401


TimeOutToken = TimeoutToken
