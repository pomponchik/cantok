from ctok.tokens.abstract_token import AbstractToken
from ctok import ConditionToken


class CounterToken(ConditionToken):
    def __init__(self, counter: int, *tokens: AbstractToken, cancelled: bool = False):
        if counter < 0:
            raise ValueError('')

        self.counter = counter

        def function() -> bool:
            if not self.counter:
                return True
            self.counter -= 1
            return False

        super().__init__(function, *tokens, cancelled=cancelled)

    def text_representation_of_superpower(self) -> str:
        return str(self.counter)
