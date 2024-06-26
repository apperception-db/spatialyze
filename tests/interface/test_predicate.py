import pytest
from spatialyze.predicate import *
from spatialyze.utils.F import *


o = objects[0]
o1 = objects[1]
o2 = objects[2]
c = camera
c0 = cameras[0]
gen = GenSqlVisitor()


@pytest.mark.parametrize("fn, sql", [
    (o, "t0.translation"),
    (o.trans, "t0.translation"),
    (o.trans, "t0.translation"),
    (o.id, "t0.itemId"),
    (o.type, "t0.objectType"),
    (o.heading, "t0.itemHeading"),

    (c, "c0.cameraTranslation"),
    (c.ego, "c0.egoTranslation"),
    (c.heading, "c0.cameraHeading"),
    (c.egoheading, "c0.egoHeading"),

    (o.trans + c, "(t0.translation+c0.cameraTranslation)"),
    (o.trans - c, "(t0.translation-c0.cameraTranslation)"),
    (o.trans * c, "(t0.translation*c0.cameraTranslation)"),
    (o.trans / c, "(t0.translation/c0.cameraTranslation)"),
    (o.trans == c, "(t0.translation=c0.cameraTranslation)"),
    (o.trans < c, "(t0.translation<c0.cameraTranslation)"),
    (o.trans > c, "(t0.translation>c0.cameraTranslation)"),
    (o.trans <= c, "(t0.translation<=c0.cameraTranslation)"),
    (o.trans >= c, "(t0.translation>=c0.cameraTranslation)"),
    (o.trans != c, "(t0.translation<>c0.cameraTranslation)"),

    (1 + c, "(1+c0.cameraTranslation)"),
    (1 - c, "(1-c0.cameraTranslation)"),
    (1 * c, "(1*c0.cameraTranslation)"),
    (1 / c, "(1/c0.cameraTranslation)"),
    (1 == c, "(c0.cameraTranslation=1)"),
    (1 < c, "(c0.cameraTranslation>1)"),
    (1 > c, "(c0.cameraTranslation<1)"),
    (1 <= c, "(c0.cameraTranslation>=1)"),
    (1 >= c, "(c0.cameraTranslation<=1)"),
    (1 != c, "(c0.cameraTranslation<>1)"),

    (lit(3), "3"),
    (lit('test', False), "test"),

    (c0.cam, "c0.cameraTranslation"),
    (cast(c0.heading, 'real'), "(c0.cameraHeading)::real"),

    (-o.trans, "(-t0.translation)"),
    (~o.trans, "(NOT t0.translation)"),
    (o.trans & o & o, "(t0.translation AND t0.translation AND t0.translation)"),
    (o.trans | o | o, "(t0.translation OR t0.translation OR t0.translation)"),
    (c.time, "c0.timestamp"),
    (arr(o.trans, o), "ARRAY[t0.translation,t0.translation]"),
    (o.bbox, "objectBBox(t0.itemId,c0.timestamp)"),
])
def test_simple_ops(fn, sql):
    assert gen(normalize(fn)) == sql


@pytest.mark.parametrize("fn, msg", [
    (AtTimeNode(o), "ObjectTableNode is illegal: ObjectTableNode[0]"),
    (o, "ObjectTableNode is illegal: ObjectTableNode[0]"),
    (c, "CameraTableNode is illegal: CameraTableNode[0]"),
    (TableNode(1), "TableNode is illegal: TableNode[1]"),
])
def test_unnormalized_node_exception(fn, msg):
    with pytest.raises(Exception) as e_info:
        gen(fn)
    assert str(e_info.value) == msg


@pytest.mark.parametrize("fn, msg", [
    (AtTimeNode(o.trans), "AtTimeNode is illegal prior NormalizeDefaultValue: AtTimeNode(attr=TableAttrNode(name='translation', table=ObjectTableNode[0], shorten=True))"),
])
def test_normalize_exception(fn, msg):
    with pytest.raises(Exception) as e_info:
        normalize(fn)
    assert str(e_info.value) == msg


@pytest.mark.parametrize("args, kwargs, msg", [
    ((1,2,3), {}, 
        "Mismatch number of arguments: expecting 2, received 3 args and 0 kwargs"),
    ((1,), {"python": 2, "extra":3},
        "Mismatch number of arguments: expecting 2, received 1 args and 2 kwargs"),
    ((1,), {"invalid":3},
        "LiteralNode does not have attribute invalid"),
])
def test_predicate_node_exception(args, kwargs, msg):
    with pytest.raises(Exception) as e_info:
        LiteralNode(*args, **kwargs)
    assert str(e_info.value) == msg


@pytest.mark.parametrize("fn, sql", [
    ((o.trans + c) - c.cam + o.type * c.ego / o, "(((t0.translation+c0.cameraTranslation)-c0.cameraTranslation)+((t0.objectType*c0.egoTranslation)/t0.translation))"),
    ((o.trans == c) & ((o < c.cam) | (o == c.ego)), "((t0.translation=c0.cameraTranslation) AND ((t0.translation<c0.cameraTranslation) OR (t0.translation=c0.egoTranslation)))"),
])
def test_nested(fn, sql):
    assert gen(normalize(fn)) == sql


@pytest.mark.parametrize("fn, sql", [
    (o.type & o.id & o.type, "(t0.objectType AND t0.itemId AND t0.objectType)"),
    (o.type | o.id | o.type, "(t0.objectType OR t0.itemId OR t0.objectType)"),
    (o.type | o.id | (o.type & c & c.ego), "(t0.objectType OR t0.itemId OR (t0.objectType AND c0.cameraTranslation AND c0.egoTranslation))"),
])
def test_expand_bool(fn, sql):
    assert gen(ExpandBoolOpTransformer()(normalize(fn))) == sql


@pytest.mark.parametrize("fn, tables, camera", [
    (o.trans & o1.trans & c.cam, {0, 1}, True),
    ((o.trans + c) - c.ego + o.trans * c.heading / o.heading, {0}, True),
    ((o.type) + o1.trans / o.heading, {0, 1}, False),
    ((o.type) + c.egoheading / o.heading, {0}, True),
])
def test_find_all_tables(fn, tables, camera):
    assert FindAllTablesVisitor()(normalize(fn)) == (tables, camera)


@pytest.mark.parametrize("fn, mapping, sql", [
    (o.trans & o1.trans & c.ego, {0:1, 1:2}, '(t1.translation AND t2.translation AND c0.egoTranslation)'),
    ((o.trans + c) - c.ego + o.type * c.heading / o1.heading, {0:1, 1:0}, '(((t1.translation+c0.cameraTranslation)-c0.egoTranslation)+((t1.objectType*c0.cameraHeading)/t0.itemHeading))'),
])
def test_map_tables(fn, mapping, sql):
    assert gen(MapTablesTransformer(mapping)(normalize(fn))) == sql


@pytest.mark.parametrize("fn, sql", [
    (arr(o.trans, c, 3), "ARRAY[t0.translation,c0.cameraTranslation,3]"),
    (arr(o.trans, [c, 3]), "ARRAY[t0.translation,[c0.cameraTranslation,3]]"),
    # (c in o.trans[1:2], "(trans IN t0.translation[1:2])"),
    # (c[o.trans[3]] in o.trans[1:2], "(trans[t0.translation[3]] IN t0.translation[1:2])"),
])
def test_array(fn, sql):
    assert gen(normalize(fn)) == sql


@pytest.mark.parametrize("resolve, out", [
    (resolve_camera_attr('test', None), "test"),
    (resolve_object_attr('test', None), "test"),
    (resolve_camera_attr('test', 1), "c1.test"),
    (resolve_object_attr('test', 3), "t3.test"),
])
def test_resolve_attr(resolve, out):
    assert resolve == out


@pytest.mark.parametrize("predicate, result", [
    (1 + stopped(o), False),
    (1 + heading_diff(o, o1), False),
    (1 + heading_diff(c, c), True),
    (1 + left_turn(o), False),
    (o.heading == 1, False),
    (c.heading == 1, True)
])
def test_is_detection_only(predicate, result):
    assert is_detection_only(predicate) == result
