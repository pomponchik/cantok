from cantok import AbstractToken
from cantok.errors import CancellationError


class SimpleToken(AbstractToken):
    exception = CancellationError

    def superpower(self) -> bool:
        return False

    def text_representation_of_superpower(self) -> str:
        return ''

    def raise_superpower_exception(self):
        self.raise_cancelled_exception()
