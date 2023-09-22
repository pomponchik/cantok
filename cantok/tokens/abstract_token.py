from abc import ABC, abstractmethod


class AbstractToken(ABC):
    def __init__(self, *tokens: 'AbstractToken', cancelled=False):
        self.tokens = tokens
        self._cancelled = cancelled

    def __repr__(self):
        other_tokens = ', '.join([repr(x) for x in self.tokens])
        if other_tokens:
            other_tokens += ', '
        superpower = self.text_representation_of_superpower()
        if superpower:
            superpower += ', '
        extra_kwargs = self.text_representation_of_extra_kwargs()
        if extra_kwargs:
            extra_kwargs = ', ' + extra_kwargs
        return f'{type(self).__name__}({superpower}{other_tokens}cancelled={self.cancelled}{extra_kwargs})'

    def __str__(self):
        cancelled_flag = 'cancelled' if self.cancelled else 'not cancelled'
        return f'<{type(self).__name__} ({cancelled_flag})>'

    def __add__(self, item: 'AbstractToken') -> 'AbstractToken':
        if not isinstance(item, AbstractToken):
            raise TypeError('Cancellation Token can only be combined with another Cancellation Token.')

        from cantok import SimpleToken

        return SimpleToken(self, item)

    @property
    def cancelled(self) -> bool:
        return self.is_cancelled()

    @cancelled.setter
    def cancelled(self, new_value) -> None:
        if new_value == True:
            self._cancelled = True
        else:
            if self._cancelled == True:
                raise ValueError('You cannot restore a cancelled token.')

    def keep_on(self) -> bool:
        return not self.is_cancelled()

    def is_cancelled(self) -> bool:
        if self._cancelled:
            return True

        elif any(x.is_cancelled_reflect() for x in self.tokens):
            return True

        elif self.superpower():
            return True

        return False

    def is_cancelled_reflect(self):
        return self.is_cancelled()

    def cancel(self) -> 'AbstractToken':
        self._cancelled = True
        return self

    @abstractmethod
    def superpower(self) -> bool:  # pragma: no cover
        pass

    @abstractmethod
    def text_representation_of_superpower(self) -> str:  # pragma: no cover
        pass

    def text_representation_of_extra_kwargs(self) -> str:
        return ''
