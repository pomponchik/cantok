from typing import Dict, Any

from cantok import AbstractToken
from cantok import ConditionToken
from cantok.errors import CounterCancellationError


class CounterToken(ConditionToken):
    exception = CounterCancellationError

    def __init__(self, counter: int, *tokens: AbstractToken, cancelled: bool = False, direct: bool = True):
        if counter < 0:
            raise ValueError('The counter must be greater than or equal to zero.')

        self.counter = counter
        self.initial_counter = counter
        self.direct = direct
        self.rollback_if_nondirect_polling = self.direct

        def function() -> bool:
            with self.lock:
                if not self.counter:
                    return True
                self.counter -= 1
                return False

        super().__init__(function, *tokens, cancelled=cancelled)

    def superpower_rollback(self, superpower_data: Dict[str, Any]) -> None:
        self.counter = superpower_data['counter']

    def text_representation_of_superpower(self) -> str:
        return str(self.counter)

    def get_extra_kwargs(self) -> Dict[str, Any]:
        return {
            'direct': self.direct,
        }

    def get_superpower_data(self) -> Dict[str, Any]:
        return {'counter': self.counter}

    def get_superpower_exception_message(self) -> str:
        return f'After {self.initial_counter} attempts, the counter was reset to zero.'
