import pytest
from spatialyze.predicate import *


o = objects[0]
o1 = objects[1]
o2 = objects[2]
c = camera
c0 = cameras[0]
gen = GenSqlVisitor()


@pytest.mark.parametrize("fn, sql", [
    (o, "valueAtTimestamp(t0.translations,c0.timestamp)"),
    (o.trans, "valueAtTimestamp(t0.translations,c0.timestamp)"),
    (o.traj, "valueAtTimestamp(t0.translations,c0.timestamp)"),
    (o.id, "t0.itemId"),
    (o.type, "t0.objectType"),
    (o.heading, "valueAtTimestamp(t0.itemHeadings,c0.timestamp)"),

    (c, "c0.cameraTranslation"),
    (c.ego, "c0.egoTranslation"),
    (c.heading, "c0.cameraHeading"),
    (c.egoheading, "c0.egoHeading"),

    (o.trans + c, "(valueAtTimestamp(t0.translations,c0.timestamp)+c0.cameraTranslation)"),
    (o.trans - c, "(valueAtTimestamp(t0.translations,c0.timestamp)-c0.cameraTranslation)"),
    (o.trans * c, "(valueAtTimestamp(t0.translations,c0.timestamp)*c0.cameraTranslation)"),
    (o.trans / c, "(valueAtTimestamp(t0.translations,c0.timestamp)/c0.cameraTranslation)"),
    (o.trans == c, "(valueAtTimestamp(t0.translations,c0.timestamp)=c0.cameraTranslation)"),
    (o.trans < c, "(valueAtTimestamp(t0.translations,c0.timestamp)<c0.cameraTranslation)"),
    (o.trans > c, "(valueAtTimestamp(t0.translations,c0.timestamp)>c0.cameraTranslation)"),
    (o.trans <= c, "(valueAtTimestamp(t0.translations,c0.timestamp)<=c0.cameraTranslation)"),
    (o.trans >= c, "(valueAtTimestamp(t0.translations,c0.timestamp)>=c0.cameraTranslation)"),
    (o.trans != c, "(valueAtTimestamp(t0.translations,c0.timestamp)<>c0.cameraTranslation)"),

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

    (-o.trans, "(-valueAtTimestamp(t0.translations,c0.timestamp))"),
    (~o.trans, "(NOT valueAtTimestamp(t0.translations,c0.timestamp))"),
    (o.trans & o & o, "(valueAtTimestamp(t0.translations,c0.timestamp) AND valueAtTimestamp(t0.translations,c0.timestamp) AND valueAtTimestamp(t0.translations,c0.timestamp))"),
    (o.trans | o | o, "(valueAtTimestamp(t0.translations,c0.timestamp) OR valueAtTimestamp(t0.translations,c0.timestamp) OR valueAtTimestamp(t0.translations,c0.timestamp))"),
    (c.time, "c0.timestamp"),
    (arr(o.trans, o), "ARRAY[valueAtTimestamp(t0.translations,c0.timestamp),valueAtTimestamp(t0.translations,c0.timestamp)]"),
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
    (AtTimeNode(o.traj), "AtTimeNode is illegal prior NormalizeDefaultValue: AtTimeNode(attr=TableAttrNode(name='translations', table=ObjectTableNode[0], shorten=True))"),
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
    ((o.trans + c) - c.cam + o.type * c.ego / o, "(((valueAtTimestamp(t0.translations,c0.timestamp)+c0.cameraTranslation)-c0.cameraTranslation)+((t0.objectType*c0.egoTranslation)/valueAtTimestamp(t0.translations,c0.timestamp)))"),
    ((o.trans == c) & ((o < c.cam) | (o == c.ego)), "((valueAtTimestamp(t0.translations,c0.timestamp)=c0.cameraTranslation) AND ((valueAtTimestamp(t0.translations,c0.timestamp)<c0.cameraTranslation) OR (valueAtTimestamp(t0.translations,c0.timestamp)=c0.egoTranslation)))"),
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
    ((o.trans + c) - c.ego + o.traj * c.heading / o.heading, {0}, True),
    ((o.type) + o1.traj / o.heading, {0, 1}, False),
    ((o.type) + c.egoheading / o.heading, {0}, True),
])
def test_find_all_tables(fn, tables, camera):
    assert FindAllTablesVisitor()(normalize(fn)) == (tables, camera)


@pytest.mark.parametrize("fn, mapping, sql", [
    (o.trans & o1.traj & c.ego, {0:1, 1:2}, '(valueAtTimestamp(t1.translations,c0.timestamp) AND valueAtTimestamp(t2.translations,c0.timestamp) AND c0.egoTranslation)'),
    ((o.trans + c) - c.ego + o.type * c.heading / o1.heading, {0:1, 1:0}, '(((valueAtTimestamp(t1.translations,c0.timestamp)+c0.cameraTranslation)-c0.egoTranslation)+((t1.objectType*c0.cameraHeading)/valueAtTimestamp(t0.itemHeadings,c0.timestamp)))'),
])
def test_map_tables(fn, mapping, sql):
    assert gen(MapTablesTransformer(mapping)(normalize(fn))) == sql


@pytest.mark.parametrize("fn, sql", [
    (arr(o.trans, c, 3), "ARRAY[valueAtTimestamp(t0.translations,c0.timestamp),c0.cameraTranslation,3]"),
    (arr(o.trans, [c, 3]), "ARRAY[valueAtTimestamp(t0.translations,c0.timestamp),[c0.cameraTranslation,3]]"),
    # (c in o.trans[1:2], "(trans IN valueAtTimestamp(t0.translations,c0.timestamp)[1:2])"),
    # (c[o.trans[3]] in o.trans[1:2], "(trans[valueAtTimestamp(t0.translations,c0.timestamp)[3]] IN valueAtTimestamp(t0.translations,c0.timestamp)[1:2])"),
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
