from cantok import AbstractToken
from cantok.errors import impossibleException


class DefaultToken(AbstractToken):
    exception = impossibleException

    def __init__(self):
        super().__init__()

    def superpower(self) -> bool:
        return False

    def text_representation_of_superpower(self) -> str:
        return ''

    def get_superpower_exception_message(self) -> str:
        return 'This exception should not be raised.'  # pragma: no cover

    @property
    def cancelled(self) -> bool:
        return False

    @cancelled.setter
    def cancelled(self, new_value: bool) -> None:
        if new_value == True:
            raise ValueError('You cannot cancel a default token.')

    def keep_on(self) -> bool:
        return True

    def is_cancelled(self, direct: bool = True) -> bool:
        return False
