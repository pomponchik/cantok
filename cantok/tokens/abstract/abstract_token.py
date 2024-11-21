from abc import ABC, abstractmethod
from sys import getrefcount
from threading import RLock
from typing import List, Dict, Awaitable, Optional, Union, Any, Literal

from cantok.errors import CancellationError
from cantok.tokens.abstract.cancel_cause import CancelCause
from cantok.tokens.abstract.coroutine_wrapper import WaitCoroutineWrapper
from cantok.tokens.abstract.report import CancellationReport
from cantok.types import IterableWithTokens


class AbstractToken(ABC):
    """Base abstract token.


    :param tokens: iterable of tokens
    :param cancelled: boolean flag indicating whether this token is cancelled, by default ``False``
    """

    # TODO: вероятно оба этих атрибута стоит сделать protected
    exception = CancellationError
    rollback_if_nondirect_polling = False

    def __init__(self, *tokens: 'AbstractToken', cancelled: bool = False) -> None:
        self.cached_report: Optional[CancellationReport] = None
        self._cancelled: bool = cancelled
        self.tokens: List[AbstractToken] = self.filter_tokens(tokens)

        # TODO: а почему именно RLock?
        #  И у меня складывается ощущение, что токены не дружат с мультипроцессингом (в частности, из-за этого лока).
        self.lock: RLock = RLock()

    def __repr__(self) -> str:
        """Print out the token representation."""
        chunks = []
        superpower = self.text_representation_of_superpower()
        if superpower:
            chunks.append(superpower)
        other_tokens = ', '.join([repr(x) for x in self.tokens])
        if other_tokens:
            chunks.append(other_tokens)
        report = self.get_report(direct=False)
        if report.cause == CancelCause.NOT_CANCELLED:
            extra_kwargs = {}
        else:
            if report.from_token is self and report.cause == CancelCause.CANCELLED:
                extra_kwargs = {'cancelled': True}
            else:
                extra_kwargs = {}
        extra_kwargs.update(**(self.get_extra_kwargs()))
        text_representation_of_extra_kwargs = self.text_representation_of_kwargs(**extra_kwargs)
        if text_representation_of_extra_kwargs:
            chunks.append(text_representation_of_extra_kwargs)

        glued_chunks = ', '.join(chunks)
        return f'{type(self).__name__}({glued_chunks})'

    def __str__(self) -> str:
        """Print out the token current status."""
        # TODO: это единственное место, где в is_cancelled передаётся direct. Этот параметр там точно нужен?
        cancelled_flag = 'cancelled' if self.is_cancelled(direct=False) else 'not cancelled'
        return f'<{type(self).__name__} ({cancelled_flag})>'

    def __add__(self, other: 'AbstractToken') -> 'AbstractToken':
        """Nest tokens in each other.

        :param other: other token to be nested.
        """
        if not isinstance(other, AbstractToken):
            raise TypeError('Cancellation Token can only be combined with another Cancellation Token.')

        from cantok import SimpleToken, DefaultToken, TimeoutToken

        if self._cancelled or other._cancelled:
            return SimpleToken(cancelled=True)

        nested_tokens = []
        container_token: Optional[AbstractToken] = None

        if isinstance(self, TimeoutToken) and isinstance(other, TimeoutToken) and self.monotonic == other.monotonic:
            if self.deadline >= other.deadline and getrefcount(self) < 4:
                if getrefcount(other) < 4:
                    other.tokens.extend(self.tokens)
                    return other
                else:
                    if self.tokens:
                        return SimpleToken(*(self.tokens), other)
                    else:
                        return other
            elif self.deadline < other.deadline and getrefcount(other) < 4:
                if getrefcount(self) < 4:
                    self.tokens.extend(other.tokens)
                    return self
                else:
                    if other.tokens:
                        return SimpleToken(*(other.tokens), self)
                    else:
                        return self

        for token in self, other:
            if isinstance(token, SimpleToken) and getrefcount(token) < 6:
                nested_tokens.extend(token.tokens)
            elif isinstance(token, DefaultToken):
                pass
            elif not isinstance(token, SimpleToken) and getrefcount(token) < 6 and container_token is None:
                container_token = token
            else:
                nested_tokens.append(token)

        if container_token is None:
            return SimpleToken(*nested_tokens)
        else:
            container_token.tokens.extend(container_token.filter_tokens(nested_tokens))
            return container_token

    # TODO: достаточно было бы дёргать за is_cancelled, которое нужно сделать геттером.
    def __bool__(self) -> bool:
        """Check the token is cancelled or not."""
        return self.keep_on()

    # TODO: как я понимаю, это тоже подкапотный метод и не нужен в публичном доступе.
    #  Тогда его стоит перевести в protected.
    @staticmethod
    def filter_tokens(tokens: IterableWithTokens) -> List['AbstractToken']:
        """Filter tokens.

        :param tokens: tokens to be filtered
        """
        from cantok import DefaultToken

        result: List[AbstractToken] = []

        for token in tokens:
            if isinstance(token, DefaultToken):
                pass
            else:
                result.append(token)

        return result

    # TODO: зачем нужен этот отдельный метод и почему он так назван?
    #  Название вводит в заблуждение, т.к. интуитивно думаешь, что это проперти, но это не так.
    #  При этом блоком ниже появляется проперти cancelled, которое дёргает за этот метод.
    #  Дальше по коду и is_cancelled, и cancelled переопределяются, что ещё больше запутывает.
    #  Я бы предложил cancelled убрать полностью, а is_cancelled сделать чистым геттером. Логи
    def is_cancelled(self, direct: bool = True) -> bool:
        """Get the token current state."""
        return self.get_report(direct=direct).cause != CancelCause.NOT_CANCELLED

    @property
    def cancelled(self) -> bool:
        """Check if the token is cancelled."""
        return self.is_cancelled()

    # TODO: зачем нам сеттер, если есть метод cancel? Я бы предложил это выпилить.
    @cancelled.setter
    def cancelled(self, new_value: Literal[True]) -> None:
        """Set the token status to `cancelled`.
        
        :param new_value: boolean flag to cancel this token.
        :raises ValueError: if the token is already cancelled.
        """
        with self.lock:
            if new_value == True:
                self._cancelled = True
            else:
                if self.is_cancelled():
                    raise ValueError('You cannot restore a cancelled token.')

    # TODO: Как я понимаю, это ещё одна обёртка над логикой is_cancelled.
    #  И, судя по всему, дальше она должна использоваться только под капотом.
    #  В этом случае было бы проще иметь is_cancelled как геттер и в остальном коде
    #  спрашивать not self.is_cancelled вместо вызовов keep_on().
    def keep_on(self) -> bool:
        """Check the token current status and reduce the token if it is not cancelled."""
        return not self.is_cancelled()

    # TODO: А зачем этот метод что-то возвращает? Ну отменили и отменили.
    #  Мы же не можем вызвать этот метод для какого-то стороннего токена через имеющийся `token.cancel(other_token)`?
    #  Так или иначе мы делаем token.cancel() и сам объект остаётся с нами.
    def cancel(self) -> 'AbstractToken':
        """Cancel the token."""
        self._cancelled = True
        return self

    # TODO: видимо, это внутренний метод и не нужен конечному пользователю.
    #  Плюс, меня постоянно смущает аргумент direct. Никак не могу понять, что он обозначает и почему так назван.
    def get_report(self, direct: bool = True) -> CancellationReport:
        """Get the report of the token current status.

        :param direct: boolean flag indicating WHAT???
        """
        if self._cancelled:
            return CancellationReport(
                cause=CancelCause.CANCELLED,
                from_token=self,
            )

        if self.check_superpower(direct):
            return CancellationReport(
                cause=CancelCause.SUPERPOWER,
                from_token=self,
            )

        if self.cached_report is not None:
            return self.cached_report

        for token in self.tokens:
            report = token.get_report(direct=False)
            if report.cause != CancelCause.NOT_CANCELLED:
                self.cached_report = report
                return report

        return CancellationReport(
            cause=CancelCause.NOT_CANCELLED,
            from_token=self,
        )

    # TODO: Зачем таймаут None? Не лучше ли 0?
    #  Избавляемся от Optional и не разрешаем сюда пихать ничего кроме int/float.
    #  Но я всё ещё не пойму, в каких случаях этот метод вообще может быть нужен.
    def wait(
            self, step: Union[int, float] = 0.0001, timeout: Optional[Union[int, float]] = None
    ) -> Awaitable:
        """Wait for token cancellation.

        :param step: number of seconds to wait before cancellation
        :param timeout: timeout in seconds
        """
        if step < 0:
            raise ValueError('The token polling iteration time cannot be less than zero.')
        if timeout is not None and timeout < 0:
            raise ValueError('The total timeout of waiting cannot be less than zero.')
        if timeout is not None and step > timeout:
            raise ValueError(
                'The total timeout of waiting cannot be less than the time of one iteration of the token polling.')

        from cantok.tokens import SimpleToken, TimeoutToken
        if timeout is None:
            token = SimpleToken()
        else:
            token = TimeoutToken(timeout)  # type: ignore[assignment]

        return WaitCoroutineWrapper(step, self + token, token)

    # TODO: А насколько вообще конечному юзеру нужно разбираться в том, почему токен отменился?
    def check(self) -> None:
        """Raise exception if token is cancelled."""
        with self.lock:
            report = self.get_report()

            if report.cause == CancelCause.CANCELLED:
                report.from_token.raise_cancelled_exception()

            elif report.cause == CancelCause.SUPERPOWER:
                report.from_token.raise_superpower_exception()









    ###########################################################################################3

    # TODO: здесь и далее я не в силах понять суть и назначение каждого метода.
    #  Но, имхо, все они должны стать protected.

    @abstractmethod
    def superpower(self) -> bool:  # pragma: no cover
        """???"""
        pass

    def superpower_rollback(self, superpower_data: Dict[str, Any]) -> None:  # pragma: no cover
        """???"""
        pass

    def check_superpower(self, direct: bool) -> bool:
        """???"""
        if self.rollback_if_nondirect_polling and not direct:
            return self.check_superpower_with_rollback()
        return self.superpower()

    def check_superpower_with_rollback(self) -> bool:
        """???"""
        with self.lock:
            superpower_data = self.get_superpower_data()
            result = self.superpower()
            self.superpower_rollback(superpower_data)
            return result

    def get_superpower_data(self) -> Dict[str, Any]:  # pragma: no cover
        """???"""
        return {}

    @abstractmethod
    def text_representation_of_superpower(self) -> str:  # pragma: no cover
        """???"""
        pass

    def get_extra_kwargs(self) -> Dict[str, Any]:
        """???"""
        return {}

    def text_representation_of_extra_kwargs(self) -> str:
        """???"""
        return self.text_representation_of_kwargs(**(self.get_extra_kwargs()))

    def text_representation_of_kwargs(self, **kwargs: Any) -> str:
        """???"""
        pairs: List[str] = [f'{key}={repr(value)}' for key, value in kwargs.items()]
        return ', '.join(pairs)

    def raise_cancelled_exception(self) -> None:
        """???"""
        raise CancellationError('The token has been cancelled.', self)

    def raise_superpower_exception(self) -> None:
        """???"""
        raise self.exception(self.get_superpower_exception_message(), self)

    @abstractmethod
    def get_superpower_exception_message(self) -> str:  # pragma: no cover
        """???"""
        return 'You have done the impossible to see this error.'
