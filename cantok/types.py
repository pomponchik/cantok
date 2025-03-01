import sys
from collections.abc import Iterable as IterableFromCollections
from typing import Iterable as IterableFromTyping

if sys.version_info >= (3, 10):
    from typing import TypeAlias  # pragma: no cover
else:
    from typing_extensions import TypeAlias  # pragma: no cover


if sys.version_info >= (3, 9):
    IterableWithTokens: TypeAlias = IterableFromCollections['AbstractToken']  # type: ignore[name-defined, unused-ignore] # pragma: no cover
else:
    IterableWithTokens = IterableFromTyping['AbstractToken']  # type: ignore[name-defined] # pragma: no cover
