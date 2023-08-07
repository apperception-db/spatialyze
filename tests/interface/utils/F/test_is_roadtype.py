import pytest
from common import *


@pytest.mark.parametrize("fn, sql", [
    (is_roadtype('intersection'), 'is_roadtype(intersection)'),
    (is_roadtype('lane'), 'is_roadtype(lane)'),
])
def test_is_roadtype(fn, sql):
    assert gen(fn) == sql
