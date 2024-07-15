from cantok import AbstractToken
from cantok.errors import ImpossibleCancelError


class DefaultToken(AbstractToken):
    exception = ImpossibleCancelError

    def __init__(self):
        super().__init__()

    def superpower(self) -> bool:
        return False

    def text_representation_of_superpower(self) -> str:
        return ''

    def get_superpower_exception_message(self) -> str:
        return 'You cannot cancel a default token.'  # pragma: no cover

    @property
    def cancelled(self) -> bool:
        return False

    @cancelled.setter
    def cancelled(self, new_value: bool) -> None:
        if new_value == True:
            raise self.raise_superpower_exception()

    def keep_on(self) -> bool:
        return True

    def is_cancelled(self, direct: bool = True) -> bool:
        return False

    def cancel(self) -> 'AbstractToken':
        raise self.raise_superpower_exception()
        raise self.exception('You cannot cancel a default token.')
