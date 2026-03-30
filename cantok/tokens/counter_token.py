from typing import Any, Dict

from cantok import AbstractToken, ConditionToken
from cantok.errors import CounterCancellationError


class CounterToken(ConditionToken):
    exception = CounterCancellationError

    def __init__(self, counter: int, *tokens: AbstractToken, cancelled: bool = False, direct: bool = True):
        if counter < 0:
            raise ValueError('The counter must be greater than or equal to zero.')

        self._initial_counter = counter
        self._direct = direct
        self._rollback_if_nondirect_polling = self._direct

        counter_bag = {'counter': counter}
        self._counter_bag = counter_bag

        def function() -> bool:
            with counter_bag['lock']:  # type: ignore[attr-defined]
                if not counter_bag['counter']:
                    return True
                counter_bag['counter'] -= 1
                return False

        super().__init__(function, *tokens, cancelled=cancelled)

        self._counter_bag['lock'] = self._lock  # type: ignore[assignment]

    @property
    def counter(self) -> int:
        return self._counter_bag['counter']

    def _superpower_rollback(self, superpower_data: Dict[str, Any]) -> None:
        self._counter_bag['counter'] = superpower_data['counter']

    def _text_representation_of_superpower(self) -> str:
        return str(self._counter_bag['counter'])

    def _get_extra_kwargs(self) -> Dict[str, Any]:
        if not self._direct:
            return {
                'direct': self._direct,
            }
        return {}

    def _get_superpower_data(self) -> Dict[str, Any]:
        return {'counter': self.counter}

    def _get_superpower_exception_message(self) -> str:
        return f'After {self._initial_counter} attempts, the counter was reset to zero.'
