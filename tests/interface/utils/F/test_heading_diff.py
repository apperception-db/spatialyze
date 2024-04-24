import pytest
from common import *


@pytest.mark.parametrize("fn, sql", [
    (heading_diff(o, o1), "(((((t0.itemHeading-t1.itemHeading))::numeric%360)+360)%360)"),
    (heading_diff(o, c),         "(((((t0.itemHeading-c0.cameraHeading))::numeric%360)+360)%360)"),
    (heading_diff(o, c.cam),     "(((((t0.itemHeading-c0.cameraHeading))::numeric%360)+360)%360)"),
    (heading_diff(o, c.heading), "(((((t0.itemHeading-c0.cameraHeading))::numeric%360)+360)%360)"),
    (heading_diff(o, c.ego),        "(((((t0.itemHeading-c0.egoHeading))::numeric%360)+360)%360)"),
    (heading_diff(o, c.egoheading), "(((((t0.itemHeading-c0.egoHeading))::numeric%360)+360)%360)"),
    (heading_diff(o, o1, between=[40, 50]), "(((((((t0.itemHeading-t1.itemHeading))::numeric%360)+360)%360)>40) AND ((((((t0.itemHeading-t1.itemHeading))::numeric%360)+360)%360)<50))"),
    (heading_diff(o, o1, between=[40+360, 50]), "(((((((t0.itemHeading-t1.itemHeading))::numeric%360)+360)%360)>40) AND ((((((t0.itemHeading-t1.itemHeading))::numeric%360)+360)%360)<50))"),
    (heading_diff(o, o1, between=[40-360, 50]), "(((((((t0.itemHeading-t1.itemHeading))::numeric%360)+360)%360)>40) AND ((((((t0.itemHeading-t1.itemHeading))::numeric%360)+360)%360)<50))"),
    (heading_diff(o, o1, between=[50, 40]), "(((((((t0.itemHeading-t1.itemHeading))::numeric%360)+360)%360)<50) OR ((((((t0.itemHeading-t1.itemHeading))::numeric%360)+360)%360)>40))"),
    (heading_diff(o, o1, excluding=[40, 50]), "(((((((t0.itemHeading-t1.itemHeading))::numeric%360)+360)%360)<40) OR ((((((t0.itemHeading-t1.itemHeading))::numeric%360)+360)%360)>50))"),
    (heading_diff(o, o1, excluding=[50, 40]), "(((((((t0.itemHeading-t1.itemHeading))::numeric%360)+360)%360)>50) AND ((((((t0.itemHeading-t1.itemHeading))::numeric%360)+360)%360)<40))"),
])
def test_heading_diff(fn, sql):
    assert gen(fn) == sql


@pytest.mark.parametrize("fn, msg", [
    (heading_diff(1, o), "LiteralNode"),
    (heading_diff(o, 1), "LiteralNode"),
    (heading_diff(o, o, test1=1, test2=2), "2"),
    (heading_diff(o, o, test1=1), "test1"),
    (heading_diff(o, o, between=1), "LiteralNode(value=1, python=True)"),
    (heading_diff(o, o, between=[1]), "1"),
    (heading_diff(o, o, between=[o, c]), "ObjectTableNode[0]"),
    (heading_diff(o, o, between=[1, c]), "CameraTableNode[0]"),
    (heading_diff(o.type, o, between=[1, c]), "ObjectTableNode[0]"),
    (heading_diff(o, distance(o, o), between=[1, c]), "CallNode"),
])
def test_exception(fn, msg):
    with pytest.raises(Exception) as e_info:
        gen(fn)
    assert str(e_info.value) == msg
