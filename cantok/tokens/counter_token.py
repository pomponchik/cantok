from typing import Dict, Any

from cantok.errors import CounterCancellationError
from cantok.tokens import ConditionToken
from cantok.tokens.abstract.abstract_token import AbstractToken


class CounterToken(ConditionToken):
    """A token that will be cancelled when the counter  is exhausted.

    CounterToken is the most ambiguous of the tokens presented by this library. Do not use it if you are not sure
    that you understand how it works correctly. However, it can be very useful in situations where you want
    to limit the number of attempts to perform an operation.

    CounterToken is initialized with an integer greater than zero. At each calculation of the answer to the question,
    whether it is canceled, this number is reduced by one. When this number becomes zero, the token is considered
    canceled.

    Example:
        .. code-block:: python

            from cantok import CounterToken

            token = CounterToken(5)

            counter = 0

            while token:

                counter += 1

            print(counter)  # 5


    The counter inside the CounterToken is reduced under one of three conditions:
        - access to the cancelled attribute.
        - calling the is_cancelled() method.
        - calling the keep_on() method.

    If you use CounterToken inside other tokens, the wrapping token can specify the status of the CounterToken.
    For security reasons, this operation does not decrease the counter. However, if you need to decrease it for
    some reason, pass ``False`` to the ``direct`` argument.

    Example:
        .. code-block:: python

            from cantok import SimpleToken, CounterToken

            first_counter_token = CounterToken(1, direct=False)

            second_counter_token = CounterToken(1, direct=True)


            print(SimpleToken(first_counter_token, second_counter_token).cancelled)  # False

            print(first_counter_token.cancelled)  # True

            print(second_counter_token.cancelled)  # False

    Like all other tokens, CounterToken can accept other tokens as parameters during initialization:

    Example:
        .. code-block:: python

            from cantok import SimpleToken, CounterToken, TimeoutToken

            token = CounterToken(15, SimpleToken(), TimeoutToken(5))

    :type: ConditionToken
    :param counter: any integer greater than zero
    :param tokens: iterable of tokens
    :param cancelled: boolean flag indicating whether this token is cancelled, by default ``False``
    :param direct: boolean flag indicating whether this token can not be decreased, by default ``True``
    """

    # TODO: лучше protected
    exception = CounterCancellationError

    def __init__(self, counter: int, *tokens: AbstractToken, cancelled: bool = False, direct: bool = True):

        if counter < 0:
            raise ValueError('The counter must be greater than or equal to zero.')

        self.initial_counter = counter
        self.direct = direct
        self.rollback_if_nondirect_polling = self.direct

        counter_bag = {'counter': counter}
        self.counter_bag = counter_bag

        # TODO: Может лучше обойтись без замыкания? Можно сделать private
        #  или вообще вынести как отдельную функцию без класса, но не вытаскивать её в общий __init.py__ для импорта.
        #  С замыканиями есть проблемы в pickle например.
        def function() -> bool:
            with counter_bag['lock']:  # type: ignore[attr-defined]
                if not counter_bag['counter']:
                    return True
                counter_bag['counter'] -= 1
                return False

        super().__init__(function, *tokens, cancelled=cancelled)

        self.counter_bag['lock'] = self.lock  # type: ignore[assignment]

    # TODO: Это действительно бывает нужно?
    @property
    def counter(self) -> int:
        """Get token's counter value.'"""
        return self.counter_bag['counter']

    # TODO: видимо в protected
    def superpower_rollback(self, superpower_data: Dict[str, Any]) -> None:
        self.counter_bag['counter'] = superpower_data['counter']

    # TODO: видимо в protected
    def text_representation_of_superpower(self) -> str:
        return str(self.counter_bag['counter'])

    # TODO: видимо в protected
    def get_extra_kwargs(self) -> Dict[str, Any]:
        if not self.direct:
            return {
                'direct': self.direct,
            }
        return {}

    # TODO: видимо в protected
    def get_superpower_data(self) -> Dict[str, Any]:
        return {'counter': self.counter}

    # TODO: видимо в protected
    def get_superpower_exception_message(self) -> str:
        return f'After {self.initial_counter} attempts, the counter was reset to zero.'
