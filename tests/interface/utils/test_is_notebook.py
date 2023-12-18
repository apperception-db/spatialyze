from spatialyze.utils.is_notebook import is_notebook


def test_is_notebook():
    assert is_notebook() == False
