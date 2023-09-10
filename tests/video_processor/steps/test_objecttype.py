import os
import pickle
import pytest

from spatialyze.predicate import *
from spatialyze.utils import F

from spatialyze.video_processor.stages.in_view.in_view import FindRoadTypes, InViewPredicate, KeepOnlyRoadTypePredicates, NormalizeInversionAndFlattenRoadTypePredicates, PushInversionInForRoadTypePredicates, InView
from spatialyze.video_processor.cache import disable_cache
from spatialyze.video_processor.stages.detection_2d.object_type_filter import FindType, ObjectTypeFilter

disable_cache()

# Test Strategies
# - Real use case -- simple predicates from the query
# - 2 format + add true/false + add ignore_roadtype
#   - x AND ~y AND (z OR ~ w)
#   - x OR ~y OR (z AND ~ w)


o = objects[0]
o1 = objects[1]
o2 = objects[2]
c = camera
c0 = cameras[0]
gen = GenSqlVisitor()
RT = '__ROADTYPES__'

@pytest.mark.parametrize("fn, types", [
    # Propagate Boolean
    (o.type & False, set()),
    (o.type | True, set()),

    (o.type | (~(o.a & False)), set()),
    (o.type & (~(o.a | True)), set()),

    (o.type & (~((o.a | True) & True)), set()),
    (arr(o.type) | (~((o.a & False) | cast(False, 'int'))), set()),

    # General
    ('car' == o.type, {'car'}),
    ((o.type == 'car') == (o1.type == 'car'), {'car'}),
])
def test_predicates(fn, types):
    _types = FindType()(fn)
    assert _types == types, (_types, types)


def test_objecttypefilter():
    assert repr(ObjectTypeFilter(types=['car', 'truck'])) == "ObjectTypeFilter(types=['car', 'truck'])"
    assert repr(ObjectTypeFilter(predicate=(o.type == 'car'))) == "ObjectTypeFilter(types=['car'])"