from cantok.tokens.abstract.abstract_token import AbstractToken
from cantok.errors import CancellationError


class SimpleToken(AbstractToken):
    """The base token is SimpleToken.

    It has no built-in automation that can cancel it. The only way to cancel SimpleToken is to explicitly
    call the cancel() method from it.

    Example:
        .. code-block:: python

            from cantok import SimpleToken

            token = SimpleToken()

            print(token.cancelled)  # False

            token.cancel()

            print(token.cancelled)  # True

    There is not much more to tell about it if you have read the story about tokens in general.

    :type: AbstractToken
    :param tokens: iterable of tokens
    :param cancelled: boolean flag indicating whether this token is cancelled, by default ``False``
    """

    # TODO: можно убрать, т.к. наследуется от AbstractToken
    exception = CancellationError

    # TODO: добавил, чтобы подсказки IDE подсвечивали аргументы в докстринге
    def __init__(self, *tokens: 'AbstractToken', cancelled: bool = False) -> None:
        super().__init__(*tokens, cancelled=cancelled)

    # TODO: лучше protected
    def superpower(self) -> bool:
        return False

    # TODO: лучше protected
    def text_representation_of_superpower(self) -> str:
        return ''

    # TODO: лучше protected
    def get_superpower_exception_message(self) -> str:
        return 'The token has been cancelled.'  # pragma: no cover
