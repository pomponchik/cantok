from cantok import AbstractToken
from cantok.errors import CancellationError


class SimpleToken(AbstractToken):
    exception = CancellationError

    def superpower(self) -> bool:
        return False

    def text_representation_of_superpower(self) -> str:
        return ''

    def get_superpower_exception_message(self) -> str:
        return 'The token has been cancelled.'  # pragma: no cover
