import pytest
from common import *


o = objects[0]
c = camera


@pytest.mark.parametrize("fn, sql", [
    (stopped(o), "(EXIT (SELECT translation FROM Item_Trajectory2 WHERE itemId = t0.itemId AND t0.frameNum + ROUND(5 * (SELECT fps FROM Spatialyze_Metadata)) = frameNum) AND ST_Distance(t0.translation,(SELECT translation FROM Item_Trajectory2 WHERE itemId = t0.itemId AND t0.frameNum + ROUND(5 * (SELECT fps FROM Spatialyze_Metadata)) = frameNum))<5)"),
    (stopped(o, distance=3.1), "(EXIT (SELECT translation FROM Item_Trajectory2 WHERE itemId = t0.itemId AND t0.frameNum + ROUND(5 * (SELECT fps FROM Spatialyze_Metadata)) = frameNum) AND ST_Distance(t0.translation,(SELECT translation FROM Item_Trajectory2 WHERE itemId = t0.itemId AND t0.frameNum + ROUND(5 * (SELECT fps FROM Spatialyze_Metadata)) = frameNum))<3.1)"),
    (stopped(o, duration=6.5), "(EXIT (SELECT translation FROM Item_Trajectory2 WHERE itemId = t0.itemId AND t0.frameNum + ROUND(6.5 * (SELECT fps FROM Spatialyze_Metadata)) = frameNum) AND ST_Distance(t0.translation,(SELECT translation FROM Item_Trajectory2 WHERE itemId = t0.itemId AND t0.frameNum + ROUND(6.5 * (SELECT fps FROM Spatialyze_Metadata)) = frameNum))<5)"),
    (stopped(o, distance=3.1, duration=6.5), "(EXIT (SELECT translation FROM Item_Trajectory2 WHERE itemId = t0.itemId AND t0.frameNum + ROUND(6.5 * (SELECT fps FROM Spatialyze_Metadata)) = frameNum) AND ST_Distance(t0.translation,(SELECT translation FROM Item_Trajectory2 WHERE itemId = t0.itemId AND t0.frameNum + ROUND(6.5 * (SELECT fps FROM Spatialyze_Metadata)) = frameNum))<3.1)"),
])
def test_stopped(fn, sql):
    assert gen(fn) == sql


@pytest.mark.parametrize("fn, msg", [
    (stopped(c), "CameraTableNode[0]"),
    (stopped(o, illegal=1), "{'illegal': LiteralNode(value=1, python=True)}"),
    (stopped(o, distance=c), "CameraTableNode[0]"),
    (stopped(o, duration=c), "CameraTableNode[0]"),
])
def test_exception(fn, msg):
    with pytest.raises(Exception) as e_info:
        gen(fn)
    assert str(e_info.value) == msg