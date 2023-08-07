import pytest
from common import *


@pytest.mark.parametrize("fn, sql", [
    (is_other_roadtype('intersection'), 'is_other_roadtype(intersection)'),
    (is_other_roadtype('lane'), 'is_other_roadtype(lane)'),
])
def test_is_other_roadtype(fn, sql):
    assert gen(fn) == sql
