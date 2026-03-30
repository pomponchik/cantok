from cantok import AbstractToken
from cantok.errors import ImpossibleCancelError


class DefaultToken(AbstractToken):
    exception = ImpossibleCancelError

    def __init__(self) -> None:
        super().__init__()

    @property
    def cancelled(self) -> bool:
        return False

    @cancelled.setter
    def cancelled(self, new_value: bool) -> None:
        if new_value == True:
            self._raise_superpower_exception()

    def keep_on(self) -> bool:
        return True

    def is_cancelled(self, direct: bool = True) -> bool:  # noqa: ARG002
        return False

    def cancel(self) -> 'AbstractToken':  # type: ignore[return]
        self._raise_superpower_exception()

    def _superpower(self) -> bool:
        return False

    def _text_representation_of_superpower(self) -> str:
        return ''

    def _get_superpower_exception_message(self) -> str:
        return 'You cannot cancel a default token.'  # pragma: no cover
