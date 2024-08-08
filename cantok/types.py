import sys
from collections.abc import Iterable


if sys.version_info > (3, 9):
    from typing import TypeAlias  # pragma: no cover
else:
    from typing_extensions import TypeAlias  # pragma: no cover

if sys.version_info > (3, 8):
    IterableWithTokens: TypeAlias = Iterable['AbstractToken']  # type: ignore[name-defined]
else:
    IterableWithTokens = Iterable  # pragma: no cover
