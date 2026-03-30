from cantok import AbstractToken
from cantok.errors import CancellationError


class SimpleToken(AbstractToken):
    """
    A basic cancellation token with no automatic cancellation condition.

    Can only be cancelled explicitly by calling cancel() or setting
    cancelled = True. Useful as a manual stop signal passed between threads.

    >>> token = SimpleToken()
    >>> token.cancel()
    >>> token.cancelled
    True
    """

    exception = CancellationError

    def _superpower(self) -> bool:
        return False

    def _text_representation_of_superpower(self) -> str:
        return ''

    def _get_superpower_exception_message(self) -> str:
        return 'The token has been cancelled.'  # pragma: no cover
