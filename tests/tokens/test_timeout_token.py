from ctok import TimeoutToken


def test_zero_timeout():
    assert TimeoutToken(0).cancelled == True
    assert TimeoutToken(0.0).cancelled == True
    assert TimeoutToken(0).is_cancelled() == True
    assert TimeoutToken(0.0).is_cancelled() == True
    assert TimeoutToken(0).keep_on() == False
    assert TimeoutToken(0.0).keep_on() == False
