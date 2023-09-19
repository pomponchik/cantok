from abc import ABC, abstractmethod


class AbstractToken(ABC):
    def __init__(self, *tokens: 'AbstractToken'):
        self.tokens = tokens
        self._cancelled = False

    @property
    def cancelled(self) -> bool:
        return self.is_cancelled()

    def keep_on(self) -> bool:
        return not self.is_cancelled()

    def is_cancelled(self) -> bool:
        if self._cancelled:
            return True

        elif any(x.is_cancelled() for x in self.tokens):
            return True

        elif self.superpower():
            return True

        return False

    def cancel(self) -> None:
        self._cancelled = True

    @abstractmethod
    def superpower(self) -> bool:
        pass
