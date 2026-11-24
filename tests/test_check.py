import api


def test_environment():
    assert api is not None
    assert 1 + 1 == 2