from blockchain_demo import create_app


def test_configuration():
    assert not create_app().testing
    assert create_app({"TESTING": True}).testing
