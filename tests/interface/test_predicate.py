import pytest
from spatialyze.predicate import *


o = objects[0]
o1 = objects[1]
o2 = objects[2]
c = camera
c0 = cameras[0]
gen = GenSqlVisitor()


@pytest.mark.parametrize("fn, sql", [
    (o.c1 + c.c1, "(t0.c1+c1)"),
    (o.c1 - c.c1, "(t0.c1-c1)"),
    (o.c1 * c.c1, "(t0.c1*c1)"),
    (o.c1 / c.c1, "(t0.c1/c1)"),
    (o.c1 == c.c1, "(t0.c1=c1)"),
    (o.c1 < c.c1, "(t0.c1<c1)"),
    (o.c1 > c.c1, "(t0.c1>c1)"),
    (o.c1 <= c.c1, "(t0.c1<=c1)"),
    (o.c1 >= c.c1, "(t0.c1>=c1)"),
    (o.c1 != c.c1, "(t0.c1<>c1)"),

    (1 + c.c1, "(1+c1)"),
    (1 - c.c1, "(1-c1)"),
    (1 * c.c1, "(1*c1)"),
    (1 / c.c1, "(1/c1)"),
    (1 == c.c1, "(c1=1)"),
    (1 < c.c1, "(c1>1)"),
    (1 > c.c1, "(c1<1)"),
    (1 <= c.c1, "(c1>=1)"),
    (1 >= c.c1, "(c1<=1)"),
    (1 != c.c1, "(c1<>1)"),

    (lit(3), "3"),
    (lit('test', False), "test"),

    (c0.c1, "c0.c1"),
    (cast(c0.c1, 'real'), "(c0.c1)::real"),

    (-o.c1, "(-t0.c1)"),
    (~o.c1, "(NOT t0.c1)"),
    (o.c1 & o.c2 & o.c3, "(t0.c1 AND t0.c2 AND t0.c3)"),
    (o.c1 | o.c2 | o.c3, "(t0.c1 OR t0.c2 OR t0.c3)"),
    (o.c1 @ c.timestamp, "valueAtTimestamp(t0.c1,timestamp)"),
    (c.timestamp @ 1, "valueAtTimestamp(timestamp,1)"),
    ([o.c1, o.c2] @ c.timestamp, "ARRAY[valueAtTimestamp(t0.c1,timestamp),valueAtTimestamp(t0.c2,timestamp)]"),
    (o.bbox @ c.timestamp, "objectBBox(t0.itemId,timestamp)"),
])
def test_simple_ops(fn, sql):
    assert gen(normalize(fn)) == sql


@pytest.mark.parametrize("args, kwargs, msg", [
    ((1,2,3), {}, 
        "Mismatch number of arguments: expecting 2, received 3 args and 0 kwargs"),
    ((1), {"python": 2, "extra":3},
        "Mismatch number of arguments: expecting 2, received 1 args and 2 kwargs"),
    ((1), {"invalid":3},
        "LiteralNode does not have attribute invalid"),
])
def test_predicate_node_exception(args, kwargs, msg):
    with pytest.raises(Exception) as e_info:
        LiteralNode(*args, **kwargs)
    str(e_info.value) == msg


@pytest.mark.parametrize("fn, sql", [
    ((o.c1 + c.c1) - c.c2 + o.c2 * c.c3 / o.c3, "(((t0.c1+c1)-c2)+((t0.c2*c3)/t0.c3))"),
    ((o.c1 == c.c1) & ((o.c2 < c.c2) | (o.c3 == c.c3)), "((t0.c1=c1) AND ((t0.c2<c2) OR (t0.c3=c3)))"),
])
def test_nested(fn, sql):
    assert gen(normalize(fn)) == sql


@pytest.mark.parametrize("fn, sql", [
    (o.c1 & o.c2 & o.c3, "(t0.c1 AND t0.c2 AND t0.c3)"),
    (o.c1 | o.c2 | o.c3, "(t0.c1 OR t0.c2 OR t0.c3)"),
    (o.c1 | o.c2 | (o.c3 & o.c4 & o.c5), "(t0.c1 OR t0.c2 OR (t0.c3 AND t0.c4 AND t0.c5))"),
])
def test_expand_bool(fn, sql):
    assert gen(ExpandBoolOpTransformer()(normalize(fn))) == sql


@pytest.mark.parametrize("fn, tables, camera", [
    (o.c1 & o1.c2 & c.c3, {0, 1}, True),
    ((o.c1 + c.c1) - c.c2 + o.c2 * c.c3 / o.c3, {0}, True),
    ((o.c1) + o1.c2 / o.c3, {0, 1}, False),
    ((o.c1) + c.c2 / o.c3, {0}, True),
])
def test_find_all_tables(fn, tables, camera):
    assert FindAllTablesVisitor()(normalize(fn)) == (tables, camera)


@pytest.mark.parametrize("fn, mapping, sql", [
    (o.c1 & o1.c2 & c.c3, {0:1, 1:2}, '(t1.c1 AND t2.c2 AND c3)'),
    ((o.c1 + c.c1) - c.c2 + o.c2 * c.c3 / o1.c3, {0:1, 1:0}, '(((t1.c1+c1)-c2)+((t1.c2*c3)/t0.c3))'),
])
def test_map_tables(fn, mapping, sql):
    assert gen(MapTablesTransformer(mapping)(normalize(fn))) == sql


@pytest.mark.parametrize("fn, sql", [
    (arr(o.c1, c.c1, 3), "ARRAY[t0.c1,c1,3]"),
    (arr(o.c1, [c.c1, 3]), "ARRAY[t0.c1,[c1,3]]"),
    # (c.c1 in o.c1[1:2], "(c1 IN t0.c1[1:2])"),
    # (c.c1[o.c1[3]] in o.c1[1:2], "(c1[t0.c1[3]] IN t0.c1[1:2])"),
])
def test_array(fn, sql):
    assert gen(fn) == sql
