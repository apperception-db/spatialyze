from spatialyze.data_types.query_result import QueryResult
from spatialyze.database import database
from spatialyze.predicate import camera, objects
from spatialyze.utils import F


def test_fig_13():
    obj1 = objects[0]
    obj2 = objects[1]
    cam = camera

    results = database.predicate(
        (obj1.id != obj2.id) &
        F.like(obj1.type, 'vehicle%') &
        F.like(obj2.type, 'vehicle%') &
        F.angle_between(F.facing_relative(cam.ego, F.road_direction(cam.ego, cam.ego)), -15, 15) &
        (F.distance(cam.ego, obj1.traj@cam.time) < 50) &
        (F.view_angle(obj1.traj@cam.time, cam.ego) < 70 / 2.0) &
        (F.distance(cam.ego, obj2.traj@cam.time) < 50) &
        (F.view_angle(obj2.traj@cam.time, cam.ego) < 70 / 2.0) &
        F.contains_all('intersection', [obj1.traj, obj2.traj]@cam.time) &
        F.angle_between(F.facing_relative(obj1.traj@cam.time, cam.ego), 50, 135) &
        F.angle_between(F.facing_relative(obj2.traj@cam.time, cam.ego), -135, -50) &
        (F.min_distance(cam.ego, F.road_segment('intersection')) < 10) &
        F.angle_between(F.facing_relative(obj1.traj@cam.time, obj2.traj@cam.time), 100, -100)
    )
    assert set(results) == set([
        QueryResult(frame_number=2, camera_id='scene-0757', filename='samples/CAM_FRONT/n008-2018-08-30-15-16-55-0400__CAM_FRONT__1535657118612404.jpg', item_ids=('b327acc1048e44889108740b2304dabc', '58350757f1d04f628aab9b22cf33549b')),
        QueryResult(frame_number=9, camera_id='scene-0757', filename='samples/CAM_FRONT/n008-2018-08-30-15-16-55-0400__CAM_FRONT__1535657128112404.jpg', item_ids=('2c74f27891164c9182d5a0d0102dca8c', 'eb28d3eeb8ac46b8ac47848a18d41dc5')),
        QueryResult(frame_number=3, camera_id='scene-0757', filename='samples/CAM_FRONT/n008-2018-08-30-15-16-55-0400__CAM_FRONT__1535657119112404.jpg', item_ids=('b327acc1048e44889108740b2304dabc', '58350757f1d04f628aab9b22cf33549b')),
        QueryResult(frame_number=1, camera_id='scene-0456', filename='samples/CAM_FRONT/n008-2018-09-18-12-07-26-0400__CAM_FRONT__1537287358412404.jpg', item_ids=('9d03c6edb6eb4d49acccb245bdd0c652', '65d120d480794b9fbb433dc58512559b')),
        QueryResult(frame_number=1, camera_id='scene-0757', filename='samples/CAM_FRONT/n008-2018-08-30-15-16-55-0400__CAM_FRONT__1535657118112404.jpg', item_ids=('82d680066ddd465dbd3b22fd6a66ed70', '58350757f1d04f628aab9b22cf33549b')),
        QueryResult(frame_number=7, camera_id='scene-0757', filename='samples/CAM_FRONT/n008-2018-08-30-15-16-55-0400__CAM_FRONT__1535657127112404.jpg', item_ids=('2c74f27891164c9182d5a0d0102dca8c', 'eb28d3eeb8ac46b8ac47848a18d41dc5')),
        QueryResult(frame_number=8, camera_id='scene-0757', filename='samples/CAM_FRONT/n008-2018-08-30-15-16-55-0400__CAM_FRONT__1535657127612404.jpg', item_ids=('2c74f27891164c9182d5a0d0102dca8c', 'eb28d3eeb8ac46b8ac47848a18d41dc5')),
        QueryResult(frame_number=1, camera_id='scene-0757', filename='samples/CAM_FRONT/n008-2018-08-30-15-16-55-0400__CAM_FRONT__1535657118112404.jpg', item_ids=('b327acc1048e44889108740b2304dabc', '58350757f1d04f628aab9b22cf33549b')),
    ])