from sys import getsizeof, version_info
from dataclasses import FrozenInstanceError

import pytest

from cantok import SimpleToken, TimeoutToken
from cantok.tokens.abstract.abstract_token import CancelCause, CancellationReport


def test_cant_change_cancellation_report():
    report = CancellationReport(
        cause=CancelCause.NOT_CANCELLED,
        from_token=SimpleToken(),
    )

    with pytest.raises(FrozenInstanceError):
        report.from_token = TimeoutToken(1)


@pytest.mark.skipif(version_info < (3, 8), reason='There is no support of __slots__ for dataclasses in old pythons.')
def test_size_of_report_is_not_so_big():
    report = CancellationReport(
        cause=CancelCause.NOT_CANCELLED,
        from_token=SimpleToken(),
    )

    assert getsizeof(report) <= 48
