from cantok.tokens.abstract.abstract_token import AbstractToken
from cantok.errors import ImpossibleCancelError


class DefaultToken(AbstractToken):
    """DefaultToken is a type of token that does not accept any arguments and cannot be cancelled.

    Otherwise, it behaves like a regular token, but if you try to cancel it, you will get an exception.

    Example:
        .. code-block:: python

            from cantok import AbstractToken, DefaultToken

            DefaultToken().cancel()  # cantok.errors.ImpossibleCancelError: You cannot cancel a default token.

    In addition, you cannot embed other tokens in DefaultToken.

    It is best to use DefaultToken as the default argument for functions:

    Example:
        .. code-block:: python

        def function(token: AbstractToken = DefaultToken()):
            ...

    :type: AbstractToken
    """

    # TODO: лучше protected
    exception = ImpossibleCancelError

    def __init__(self) -> None:
        super().__init__()

    # TODO: лучше protected
    def superpower(self) -> bool:
        return False

    # TODO: лучше protected
    def text_representation_of_superpower(self) -> str:
        return ''

    # TODO: лучше protected
    def get_superpower_exception_message(self) -> str:
        return 'You cannot cancel a default token.'  # pragma: no cover

    # TODO: См. в abstract token
    @property
    def cancelled(self) -> bool:
        return False

    # TODO: См. в abstract token
    @cancelled.setter
    def cancelled(self, new_value: bool) -> None:
        if new_value == True:
            self.raise_superpower_exception()

    # TODO: См. в abstract token
    def keep_on(self) -> bool:
        return True

    # TODO: См. в abstract token
    def is_cancelled(self, direct: bool = True) -> bool:
        return False

    def cancel(self) -> None:
        """Try to cancel the default token."""
        self.raise_superpower_exception()
