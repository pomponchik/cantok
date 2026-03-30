from cantok.errors import CancellationError as CancellationError
from cantok.errors import ConditionCancellationError as ConditionCancellationError
from cantok.errors import CounterCancellationError as CounterCancellationError
from cantok.errors import ImpossibleCancelError as ImpossibleCancelError
from cantok.errors import TimeoutCancellationError as TimeoutCancellationError
from cantok.tokens.abstract.abstract_token import (
    AbstractToken as AbstractToken,
)
from cantok.tokens.condition_token import ConditionToken as ConditionToken
from cantok.tokens.counter_token import CounterToken as CounterToken
from cantok.tokens.default_token import DefaultToken as DefaultToken
from cantok.tokens.simple_token import SimpleToken as SimpleToken
from cantok.tokens.timeout_token import TimeoutToken as TimeoutToken

TimeOutToken = TimeoutToken
