from typing import Dict
from dataclasses import dataclass
from sys import version_info

from cantok.tokens.abstract.cancel_cause import CancelCause


if version_info >= (3, 10):
    addictional_fields: Dict[str, bool] = {'slots': True}
else:
    addictional_fields = {}

@dataclass(frozen=True, **addictional_fields)  # type: ignore[call-overload, unused-ignore]
class CancellationReport:
    cause: CancelCause
    from_token: 'AbstractToken'  # type: ignore[name-defined]
