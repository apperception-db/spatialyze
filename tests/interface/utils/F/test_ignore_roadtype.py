import pytest
from common import *


@pytest.mark.parametrize("fn, sql", [
    (ignore_roadtype(), 'ignore_roadtype()'),
])
def test_ignore_roadtype(fn, sql):
    assert gen(fn) == sql
