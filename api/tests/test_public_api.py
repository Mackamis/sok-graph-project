import api


def test_all_public_names_are_importable():
    for name in getattr(api, "__all__"):
        assert hasattr(api, name), f"{name!r} is listed in api.__all__ but not importable"
