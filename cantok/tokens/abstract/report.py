from dataclasses import dataclass
from sys import version_info
from typing import Dict

from cantok.tokens.abstract.cancel_cause import CancelCause

if version_info >= (3, 10):
    additional_fields: Dict[str, bool] = {'slots': True}  # pragma: no cover
else:
    additional_fields = {}  # pragma: no cover

@dataclass(frozen=True, **additional_fields)  # type: ignore[call-overload, unused-ignore]
class CancellationReport:
    cause: CancelCause
    from_token: 'AbstractToken'  # type: ignore[name-defined]
