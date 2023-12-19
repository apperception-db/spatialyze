from spatialyze.data_types.query_result import QueryResult
from spatialyze.database import database
from spatialyze.predicate import objects, camera
from spatialyze.utils import F
import datetime as datetime


def test_fig_12():
    o = objects[0]
    c = camera
    results = database.predicate(
        F.like(o.type, 'human.pedestrian%') &
        F.contains('road', c.ego) &
        (F.contained_margin(o.bbox, F.road_segment('road'), 0.50) | F.contains('road', o)) &
        F.heading_diff(o, c.ego, excluding=[-70, 70]) &
        F.heading_diff(c.ego, F.road_direction(c.ego, c.ego), between=[-15, 15]) &
        (F.distance(c, o) < 50) &
        (F.view_angle(o, c) < 35)
    )

    assert set(results) == set([
        # QueryResult(frame_number=1, camera_id='scene-0168', filename='samples/CAM_FRONT/n008-2018-05-21-11-06-59-0400__CAM_FRONT__1526915471412465.jpg', item_ids=('c6e303c0a71b49d99626a80fd0b4e827',)),
        # QueryResult(frame_number=1, camera_id='scene-0224', filename='samples/CAM_FRONT/n008-2018-07-27-12-07-38-0400__CAM_FRONT__1532707917112404.jpg', item_ids=('371c4fb1a7454570a6bdacdbbcdd7d5c',)),
        # QueryResult(frame_number=1, camera_id='scene-0284', filename='samples/CAM_FRONT/n008-2018-08-31-11-19-57-0400__CAM_FRONT__1535728830362404.jpg', item_ids=('b24a5fea4d534aa79e9190d96ba62e39',)),
        # QueryResult(frame_number=1, camera_id='scene-0392', filename='samples/CAM_FRONT/n008-2018-08-31-11-56-46-0400__CAM_FRONT__1535731236162404.jpg', item_ids=('1fcd6a77d18e4a579e905e29f314e8b7',)),
        # QueryResult(frame_number=1, camera_id='scene-0746', filename='samples/CAM_FRONT/n008-2018-08-30-15-16-55-0400__CAM_FRONT__1535656805162404.jpg', item_ids=('9fff49bd2ddb4719ad65a60d9ae6df63',)),
        # QueryResult(frame_number=1, camera_id='scene-0746', filename='samples/CAM_FRONT/n008-2018-08-30-15-16-55-0400__CAM_FRONT__1535656805162404.jpg', item_ids=('baae5f7bd0b8432eac525991a9cc9b69',)),
        # QueryResult(frame_number=1, camera_id='scene-0813', filename='samples/CAM_FRONT/n008-2018-09-18-15-26-58-0400__CAM_FRONT__1537299143862404.jpg', item_ids=('7244ef2d7394451abfeb57bb33de8adb',)),
        # QueryResult(frame_number=2, camera_id='scene-0392', filename='samples/CAM_FRONT/n008-2018-08-31-11-56-46-0400__CAM_FRONT__1535731236662404.jpg', item_ids=('1fcd6a77d18e4a579e905e29f314e8b7',)),
        # QueryResult(frame_number=2, camera_id='scene-0746', filename='samples/CAM_FRONT/n008-2018-08-30-15-16-55-0400__CAM_FRONT__1535656805662415.jpg', item_ids=('9fff49bd2ddb4719ad65a60d9ae6df63',)),
        # QueryResult(frame_number=2, camera_id='scene-0746', filename='samples/CAM_FRONT/n008-2018-08-30-15-16-55-0400__CAM_FRONT__1535656805662415.jpg', item_ids=('baae5f7bd0b8432eac525991a9cc9b69',)),
        # QueryResult(frame_number=2, camera_id='scene-0813', filename='samples/CAM_FRONT/n008-2018-09-18-15-26-58-0400__CAM_FRONT__1537299144362404.jpg', item_ids=('7244ef2d7394451abfeb57bb33de8adb',)),
        # QueryResult(frame_number=3, camera_id='scene-0392', filename='samples/CAM_FRONT/n008-2018-08-31-11-56-46-0400__CAM_FRONT__1535731237112404.jpg', item_ids=('1fcd6a77d18e4a579e905e29f314e8b7',)),
        # QueryResult(frame_number=3, camera_id='scene-0746', filename='samples/CAM_FRONT/n008-2018-08-30-15-16-55-0400__CAM_FRONT__1535656806162404.jpg', item_ids=('9fff49bd2ddb4719ad65a60d9ae6df63',)),
        # QueryResult(frame_number=3, camera_id='scene-0746', filename='samples/CAM_FRONT/n008-2018-08-30-15-16-55-0400__CAM_FRONT__1535656806162404.jpg', item_ids=('baae5f7bd0b8432eac525991a9cc9b69',)),
        # QueryResult(frame_number=3, camera_id='scene-0813', filename='samples/CAM_FRONT/n008-2018-09-18-15-26-58-0400__CAM_FRONT__1537299144862404.jpg', item_ids=('7244ef2d7394451abfeb57bb33de8adb',)),
        # QueryResult(frame_number=4, camera_id='scene-0392', filename='samples/CAM_FRONT/n008-2018-08-31-11-56-46-0400__CAM_FRONT__1535731237612404.jpg', item_ids=('1fcd6a77d18e4a579e905e29f314e8b7',)),
        # QueryResult(frame_number=4, camera_id='scene-0598', filename='samples/CAM_FRONT/n008-2018-09-18-13-41-50-0400__CAM_FRONT__1537293291162404.jpg', item_ids=('f98255abcaa4448f8e8293516f45c47a',)),
        # QueryResult(frame_number=4, camera_id='scene-0658', filename='samples/CAM_FRONT/n008-2018-08-27-11-48-51-0400__CAM_FRONT__1535385153662404.jpg', item_ids=('c24e096fcf4c4e55b74892bddc982eaa',)),
        # QueryResult(frame_number=4, camera_id='scene-0746', filename='samples/CAM_FRONT/n008-2018-08-30-15-16-55-0400__CAM_FRONT__1535656806612404.jpg', item_ids=('9fff49bd2ddb4719ad65a60d9ae6df63',)),
        # QueryResult(frame_number=4, camera_id='scene-0746', filename='samples/CAM_FRONT/n008-2018-08-30-15-16-55-0400__CAM_FRONT__1535656806612404.jpg', item_ids=('baae5f7bd0b8432eac525991a9cc9b69',)),
        # QueryResult(frame_number=4, camera_id='scene-0813', filename='samples/CAM_FRONT/n008-2018-09-18-15-26-58-0400__CAM_FRONT__1537299145362404.jpg', item_ids=('7244ef2d7394451abfeb57bb33de8adb',)),
        # QueryResult(frame_number=5, camera_id='scene-0301', filename='samples/CAM_FRONT/n008-2018-08-31-11-19-57-0400__CAM_FRONT__1535729326912404.jpg', item_ids=('1b2ffdc364c0402dad9decd6290fbb47',)),
        # QueryResult(frame_number=5, camera_id='scene-0598', filename='samples/CAM_FRONT/n008-2018-09-18-13-41-50-0400__CAM_FRONT__1537293291662404.jpg', item_ids=('f98255abcaa4448f8e8293516f45c47a',)),
        # QueryResult(frame_number=5, camera_id='scene-0658', filename='samples/CAM_FRONT/n008-2018-08-27-11-48-51-0400__CAM_FRONT__1535385154162404.jpg', item_ids=('69c08f8de9eb4af1ade1a6f85f9421fd',)),
        # QueryResult(frame_number=5, camera_id='scene-0658', filename='samples/CAM_FRONT/n008-2018-08-27-11-48-51-0400__CAM_FRONT__1535385154162404.jpg', item_ids=('c24e096fcf4c4e55b74892bddc982eaa',)),
        # QueryResult(frame_number=5, camera_id='scene-0746', filename='samples/CAM_FRONT/n008-2018-08-30-15-16-55-0400__CAM_FRONT__1535656807162404.jpg', item_ids=('9fff49bd2ddb4719ad65a60d9ae6df63',)),
        # QueryResult(frame_number=5, camera_id='scene-0813', filename='samples/CAM_FRONT/n008-2018-09-18-15-26-58-0400__CAM_FRONT__1537299145862404.jpg', item_ids=('7244ef2d7394451abfeb57bb33de8adb',)),
        # QueryResult(frame_number=5, camera_id='scene-0816', filename='samples/CAM_FRONT/n008-2018-09-18-15-26-58-0400__CAM_FRONT__1537299229362404.jpg', item_ids=('2fe325de43054797a1b6c92e4bbac3bb',)),
        # QueryResult(frame_number=6, camera_id='scene-0301', filename='samples/CAM_FRONT/n008-2018-08-31-11-19-57-0400__CAM_FRONT__1535729327412404.jpg', item_ids=('1b2ffdc364c0402dad9decd6290fbb47',)),
        # QueryResult(frame_number=6, camera_id='scene-0598', filename='samples/CAM_FRONT/n008-2018-09-18-13-41-50-0400__CAM_FRONT__1537293292162404.jpg', item_ids=('f98255abcaa4448f8e8293516f45c47a',)),
        # QueryResult(frame_number=6, camera_id='scene-0658', filename='samples/CAM_FRONT/n008-2018-08-27-11-48-51-0400__CAM_FRONT__1535385154662404.jpg', item_ids=('69c08f8de9eb4af1ade1a6f85f9421fd',)),
        # QueryResult(frame_number=6, camera_id='scene-0658', filename='samples/CAM_FRONT/n008-2018-08-27-11-48-51-0400__CAM_FRONT__1535385154662404.jpg', item_ids=('c24e096fcf4c4e55b74892bddc982eaa',)),
        # QueryResult(frame_number=6, camera_id='scene-0746', filename='samples/CAM_FRONT/n008-2018-08-30-15-16-55-0400__CAM_FRONT__1535656807662404.jpg', item_ids=('9fff49bd2ddb4719ad65a60d9ae6df63',)),
        # QueryResult(frame_number=6, camera_id='scene-0813', filename='samples/CAM_FRONT/n008-2018-09-18-15-26-58-0400__CAM_FRONT__1537299146362404.jpg', item_ids=('7244ef2d7394451abfeb57bb33de8adb',)),
        # QueryResult(frame_number=7, camera_id='scene-0301', filename='samples/CAM_FRONT/n008-2018-08-31-11-19-57-0400__CAM_FRONT__1535729327912404.jpg', item_ids=('1b2ffdc364c0402dad9decd6290fbb47',)),
        # QueryResult(frame_number=7, camera_id='scene-0598', filename='samples/CAM_FRONT/n008-2018-09-18-13-41-50-0400__CAM_FRONT__1537293292662404.jpg', item_ids=('f98255abcaa4448f8e8293516f45c47a',)),
        # QueryResult(frame_number=7, camera_id='scene-0658', filename='samples/CAM_FRONT/n008-2018-08-27-11-48-51-0400__CAM_FRONT__1535385155162404.jpg', item_ids=('69c08f8de9eb4af1ade1a6f85f9421fd',)),
        # QueryResult(frame_number=7, camera_id='scene-0658', filename='samples/CAM_FRONT/n008-2018-08-27-11-48-51-0400__CAM_FRONT__1535385155162404.jpg', item_ids=('c24e096fcf4c4e55b74892bddc982eaa',)),
        # QueryResult(frame_number=7, camera_id='scene-0746', filename='samples/CAM_FRONT/n008-2018-08-30-15-16-55-0400__CAM_FRONT__1535656808162404.jpg', item_ids=('9fff49bd2ddb4719ad65a60d9ae6df63',)),
        # QueryResult(frame_number=7, camera_id='scene-0813', filename='samples/CAM_FRONT/n008-2018-09-18-15-26-58-0400__CAM_FRONT__1537299146862404.jpg', item_ids=('7244ef2d7394451abfeb57bb33de8adb',)),
        # QueryResult(frame_number=7, camera_id='scene-0816', filename='samples/CAM_FRONT/n008-2018-09-18-15-26-58-0400__CAM_FRONT__1537299239112404.jpg', item_ids=('fad9ff01047349a595412ba5be48ad41',)),
        # QueryResult(frame_number=8, camera_id='scene-0301', filename='samples/CAM_FRONT/n008-2018-08-31-11-19-57-0400__CAM_FRONT__1535729328412404.jpg', item_ids=('1b2ffdc364c0402dad9decd6290fbb47',)),
        # QueryResult(frame_number=8, camera_id='scene-0541', filename='samples/CAM_FRONT/n008-2018-08-30-15-52-26-0400__CAM_FRONT__1535659404362404.jpg', item_ids=('e8a2ed72b3554c98b18f6b20530a7020',)),
        # QueryResult(frame_number=8, camera_id='scene-0598', filename='samples/CAM_FRONT/n008-2018-09-18-13-41-50-0400__CAM_FRONT__1537293293162404.jpg', item_ids=('f98255abcaa4448f8e8293516f45c47a',)),
        # QueryResult(frame_number=8, camera_id='scene-0658', filename='samples/CAM_FRONT/n008-2018-08-27-11-48-51-0400__CAM_FRONT__1535385158662404.jpg', item_ids=('69c08f8de9eb4af1ade1a6f85f9421fd',)),
        # QueryResult(frame_number=8, camera_id='scene-0658', filename='samples/CAM_FRONT/n008-2018-08-27-11-48-51-0400__CAM_FRONT__1535385158662404.jpg', item_ids=('c24e096fcf4c4e55b74892bddc982eaa',)),
        # QueryResult(frame_number=8, camera_id='scene-0813', filename='samples/CAM_FRONT/n008-2018-09-18-15-26-58-0400__CAM_FRONT__1537299147362404.jpg', item_ids=('7244ef2d7394451abfeb57bb33de8adb',)),
        # QueryResult(frame_number=8, camera_id='scene-0816', filename='samples/CAM_FRONT/n008-2018-09-18-15-26-58-0400__CAM_FRONT__1537299240112404.jpg', item_ids=('fad9ff01047349a595412ba5be48ad41',)),
        # QueryResult(frame_number=9, camera_id='scene-0301', filename='samples/CAM_FRONT/n008-2018-08-31-11-19-57-0400__CAM_FRONT__1535729328912404.jpg', item_ids=('1b2ffdc364c0402dad9decd6290fbb47',)),
        # QueryResult(frame_number=9, camera_id='scene-0541', filename='samples/CAM_FRONT/n008-2018-08-30-15-52-26-0400__CAM_FRONT__1535659404762404.jpg', item_ids=('e8a2ed72b3554c98b18f6b20530a7020',)),
        # QueryResult(frame_number=9, camera_id='scene-0598', filename='samples/CAM_FRONT/n008-2018-09-18-13-41-50-0400__CAM_FRONT__1537293293662404.jpg', item_ids=('f98255abcaa4448f8e8293516f45c47a',)),
        # QueryResult(frame_number=9, camera_id='scene-0658', filename='samples/CAM_FRONT/n008-2018-08-27-11-48-51-0400__CAM_FRONT__1535385159162404.jpg', item_ids=('c24e096fcf4c4e55b74892bddc982eaa',)),
        # QueryResult(frame_number=9, camera_id='scene-0813', filename='samples/CAM_FRONT/n008-2018-09-18-15-26-58-0400__CAM_FRONT__1537299147862404.jpg', item_ids=('7244ef2d7394451abfeb57bb33de8adb',)),
        # QueryResult(frame_number=10, camera_id='scene-0301', filename='samples/CAM_FRONT/n008-2018-08-31-11-19-57-0400__CAM_FRONT__1535729329412404.jpg', item_ids=('1b2ffdc364c0402dad9decd6290fbb47',)),
        # QueryResult(frame_number=10, camera_id='scene-0541', filename='samples/CAM_FRONT/n008-2018-08-30-15-52-26-0400__CAM_FRONT__1535659405262404.jpg', item_ids=('e8a2ed72b3554c98b18f6b20530a7020',)),
        # QueryResult(frame_number=10, camera_id='scene-0658', filename='samples/CAM_FRONT/n008-2018-08-27-11-48-51-0400__CAM_FRONT__1535385159662404.jpg', item_ids=('c24e096fcf4c4e55b74892bddc982eaa',)),
        # QueryResult(frame_number=10, camera_id='scene-0813', filename='samples/CAM_FRONT/n008-2018-09-18-15-26-58-0400__CAM_FRONT__1537299148362404.jpg', item_ids=('7244ef2d7394451abfeb57bb33de8adb',)),
        # QueryResult(frame_number=11, camera_id='scene-0301', filename='samples/CAM_FRONT/n008-2018-08-31-11-19-57-0400__CAM_FRONT__1535729329912795.jpg', item_ids=('1b2ffdc364c0402dad9decd6290fbb47',)),
        # QueryResult(frame_number=11, camera_id='scene-0541', filename='samples/CAM_FRONT/n008-2018-08-30-15-52-26-0400__CAM_FRONT__1535659405762404.jpg', item_ids=('e8a2ed72b3554c98b18f6b20530a7020',)),
        # QueryResult(frame_number=11, camera_id='scene-0813', filename='samples/CAM_FRONT/n008-2018-09-18-15-26-58-0400__CAM_FRONT__1537299148862404.jpg', item_ids=('7244ef2d7394451abfeb57bb33de8adb',)),
        # QueryResult(frame_number=12, camera_id='scene-0301', filename='samples/CAM_FRONT/n008-2018-08-31-11-19-57-0400__CAM_FRONT__1535729330362404.jpg', item_ids=('1b2ffdc364c0402dad9decd6290fbb47',)),
        # QueryResult(frame_number=12, camera_id='scene-0813', filename='samples/CAM_FRONT/n008-2018-09-18-15-26-58-0400__CAM_FRONT__1537299149412404.jpg', item_ids=('7244ef2d7394451abfeb57bb33de8adb',)),
        # QueryResult(frame_number=15, camera_id='scene-0557', filename='samples/CAM_FRONT/n008-2018-08-31-11-37-23-0400__CAM_FRONT__1535730293412404.jpg', item_ids=('93447c5bd75b4862995b0a4b12b0459f',)),
    ])


def test_fig_12_new():
    o = objects[0]
    c = camera
    results = database.predicate(
        F.like(o.type, 'human.pedestrian%') &
        F.contains('road', c.ego) &
        (F.contained_margin(o.bbox, F.road_segment('road'), 0.50) | F.contains('road', o)) &
        F.heading_diff(o, c.ego, between=[-70, 70]) &
        F.heading_diff(c.ego, F.road_direction(c.ego, c.ego), between=[-15, 15]) &
        (F.distance(c, o) < 50) &
        (F.view_angle(o, c) < 35)
    )

    assert set(results) == set([
        QueryResult(frame_number=1, camera_id='scene-0168', filename='samples/CAM_FRONT/n008-2018-05-21-11-06-59-0400__CAM_FRONT__1526915471412465.jpg', item_ids=('c6e303c0a71b49d99626a80fd0b4e827',)),
        QueryResult(frame_number=1, camera_id='scene-0202', filename='samples/CAM_FRONT/n008-2018-07-26-12-13-50-0400__CAM_FRONT__1532621788662404.jpg', item_ids=('e43cda5a1c654be3b90f9db8b96581c2',)),
        QueryResult(frame_number=1, camera_id='scene-0224', filename='samples/CAM_FRONT/n008-2018-07-27-12-07-38-0400__CAM_FRONT__1532707917112404.jpg', item_ids=('371c4fb1a7454570a6bdacdbbcdd7d5c',)),
        QueryResult(frame_number=1, camera_id='scene-0226', filename='samples/CAM_FRONT/n008-2018-07-27-12-07-38-0400__CAM_FRONT__1532708010412404.jpg', item_ids=('001af0f00b314abc89adcc5641c4772b',)),
        QueryResult(frame_number=1, camera_id='scene-0284', filename='samples/CAM_FRONT/n008-2018-08-31-11-19-57-0400__CAM_FRONT__1535728830362404.jpg', item_ids=('b24a5fea4d534aa79e9190d96ba62e39',)),
        QueryResult(frame_number=1, camera_id='scene-0328', filename='samples/CAM_FRONT/n008-2018-08-27-11-48-51-0400__CAM_FRONT__1535385460012404.jpg', item_ids=('727067ea67a141a38a6290a96fbb9bf5',)),
        QueryResult(frame_number=1, camera_id='scene-0392', filename='samples/CAM_FRONT/n008-2018-08-31-11-56-46-0400__CAM_FRONT__1535731236162404.jpg', item_ids=('1fcd6a77d18e4a579e905e29f314e8b7',)),
        QueryResult(frame_number=1, camera_id='scene-0746', filename='samples/CAM_FRONT/n008-2018-08-30-15-16-55-0400__CAM_FRONT__1535656805162404.jpg', item_ids=('baae5f7bd0b8432eac525991a9cc9b69',)),
        QueryResult(frame_number=1, camera_id='scene-0813', filename='samples/CAM_FRONT/n008-2018-09-18-15-26-58-0400__CAM_FRONT__1537299143862404.jpg', item_ids=('7244ef2d7394451abfeb57bb33de8adb',)),
        QueryResult(frame_number=2, camera_id='scene-0226', filename='samples/CAM_FRONT/n008-2018-07-27-12-07-38-0400__CAM_FRONT__1532708011362404.jpg', item_ids=('001af0f00b314abc89adcc5641c4772b',)),
        QueryResult(frame_number=2, camera_id='scene-0392', filename='samples/CAM_FRONT/n008-2018-08-31-11-56-46-0400__CAM_FRONT__1535731236662404.jpg', item_ids=('1fcd6a77d18e4a579e905e29f314e8b7',)),
        QueryResult(frame_number=2, camera_id='scene-0746', filename='samples/CAM_FRONT/n008-2018-08-30-15-16-55-0400__CAM_FRONT__1535656805662415.jpg', item_ids=('baae5f7bd0b8432eac525991a9cc9b69',)),
        QueryResult(frame_number=2, camera_id='scene-0813', filename='samples/CAM_FRONT/n008-2018-09-18-15-26-58-0400__CAM_FRONT__1537299144362404.jpg', item_ids=('7244ef2d7394451abfeb57bb33de8adb',)),
        QueryResult(frame_number=3, camera_id='scene-0070', filename='samples/CAM_FRONT/n008-2018-08-01-15-52-19-0400__CAM_FRONT__1533153530662404.jpg', item_ids=('4424dc027f6646178b218081a9b27233',)),
        QueryResult(frame_number=3, camera_id='scene-0392', filename='samples/CAM_FRONT/n008-2018-08-31-11-56-46-0400__CAM_FRONT__1535731237112404.jpg', item_ids=('1fcd6a77d18e4a579e905e29f314e8b7',)),
        QueryResult(frame_number=3, camera_id='scene-0746', filename='samples/CAM_FRONT/n008-2018-08-30-15-16-55-0400__CAM_FRONT__1535656806162404.jpg', item_ids=('9fff49bd2ddb4719ad65a60d9ae6df63',)),
        QueryResult(frame_number=3, camera_id='scene-0746', filename='samples/CAM_FRONT/n008-2018-08-30-15-16-55-0400__CAM_FRONT__1535656806162404.jpg', item_ids=('baae5f7bd0b8432eac525991a9cc9b69',)),
        QueryResult(frame_number=3, camera_id='scene-0813', filename='samples/CAM_FRONT/n008-2018-09-18-15-26-58-0400__CAM_FRONT__1537299144862404.jpg', item_ids=('7244ef2d7394451abfeb57bb33de8adb',)),
        QueryResult(frame_number=4, camera_id='scene-0070', filename='samples/CAM_FRONT/n008-2018-08-01-15-52-19-0400__CAM_FRONT__1533153531162404.jpg', item_ids=('4424dc027f6646178b218081a9b27233',)),
        QueryResult(frame_number=4, camera_id='scene-0392', filename='samples/CAM_FRONT/n008-2018-08-31-11-56-46-0400__CAM_FRONT__1535731237612404.jpg', item_ids=('1fcd6a77d18e4a579e905e29f314e8b7',)),
        QueryResult(frame_number=4, camera_id='scene-0598', filename='samples/CAM_FRONT/n008-2018-09-18-13-41-50-0400__CAM_FRONT__1537293291162404.jpg', item_ids=('f98255abcaa4448f8e8293516f45c47a',)),
        QueryResult(frame_number=4, camera_id='scene-0746', filename='samples/CAM_FRONT/n008-2018-08-30-15-16-55-0400__CAM_FRONT__1535656806612404.jpg', item_ids=('9fff49bd2ddb4719ad65a60d9ae6df63',)),
        QueryResult(frame_number=4, camera_id='scene-0746', filename='samples/CAM_FRONT/n008-2018-08-30-15-16-55-0400__CAM_FRONT__1535656806612404.jpg', item_ids=('baae5f7bd0b8432eac525991a9cc9b69',)),
        QueryResult(frame_number=4, camera_id='scene-0813', filename='samples/CAM_FRONT/n008-2018-09-18-15-26-58-0400__CAM_FRONT__1537299145362404.jpg', item_ids=('7244ef2d7394451abfeb57bb33de8adb',)),
        QueryResult(frame_number=5, camera_id='scene-0070', filename='samples/CAM_FRONT/n008-2018-08-01-15-52-19-0400__CAM_FRONT__1533153531662404.jpg', item_ids=('4424dc027f6646178b218081a9b27233',)),
        QueryResult(frame_number=5, camera_id='scene-0301', filename='samples/CAM_FRONT/n008-2018-08-31-11-19-57-0400__CAM_FRONT__1535729326912404.jpg', item_ids=('1b2ffdc364c0402dad9decd6290fbb47',)),
        QueryResult(frame_number=5, camera_id='scene-0598', filename='samples/CAM_FRONT/n008-2018-09-18-13-41-50-0400__CAM_FRONT__1537293291662404.jpg', item_ids=('f98255abcaa4448f8e8293516f45c47a',)),
        QueryResult(frame_number=5, camera_id='scene-0658', filename='samples/CAM_FRONT/n008-2018-08-27-11-48-51-0400__CAM_FRONT__1535385154162404.jpg', item_ids=('69c08f8de9eb4af1ade1a6f85f9421fd',)),
        QueryResult(frame_number=5, camera_id='scene-0658', filename='samples/CAM_FRONT/n008-2018-08-27-11-48-51-0400__CAM_FRONT__1535385154162404.jpg', item_ids=('c24e096fcf4c4e55b74892bddc982eaa',)),
        QueryResult(frame_number=5, camera_id='scene-0746', filename='samples/CAM_FRONT/n008-2018-08-30-15-16-55-0400__CAM_FRONT__1535656807162404.jpg', item_ids=('9fff49bd2ddb4719ad65a60d9ae6df63',)),
        QueryResult(frame_number=5, camera_id='scene-0813', filename='samples/CAM_FRONT/n008-2018-09-18-15-26-58-0400__CAM_FRONT__1537299145862404.jpg', item_ids=('7244ef2d7394451abfeb57bb33de8adb',)),
        QueryResult(frame_number=5, camera_id='scene-0816', filename='samples/CAM_FRONT/n008-2018-09-18-15-26-58-0400__CAM_FRONT__1537299229362404.jpg', item_ids=('2fe325de43054797a1b6c92e4bbac3bb',)),
        QueryResult(frame_number=6, camera_id='scene-0301', filename='samples/CAM_FRONT/n008-2018-08-31-11-19-57-0400__CAM_FRONT__1535729327412404.jpg', item_ids=('1b2ffdc364c0402dad9decd6290fbb47',)),
        QueryResult(frame_number=6, camera_id='scene-0598', filename='samples/CAM_FRONT/n008-2018-09-18-13-41-50-0400__CAM_FRONT__1537293292162404.jpg', item_ids=('f98255abcaa4448f8e8293516f45c47a',)),
        QueryResult(frame_number=6, camera_id='scene-0658', filename='samples/CAM_FRONT/n008-2018-08-27-11-48-51-0400__CAM_FRONT__1535385154662404.jpg', item_ids=('69c08f8de9eb4af1ade1a6f85f9421fd',)),
        QueryResult(frame_number=6, camera_id='scene-0658', filename='samples/CAM_FRONT/n008-2018-08-27-11-48-51-0400__CAM_FRONT__1535385154662404.jpg', item_ids=('c24e096fcf4c4e55b74892bddc982eaa',)),
        QueryResult(frame_number=6, camera_id='scene-0746', filename='samples/CAM_FRONT/n008-2018-08-30-15-16-55-0400__CAM_FRONT__1535656807662404.jpg', item_ids=('9fff49bd2ddb4719ad65a60d9ae6df63',)),
        QueryResult(frame_number=6, camera_id='scene-0813', filename='samples/CAM_FRONT/n008-2018-09-18-15-26-58-0400__CAM_FRONT__1537299146362404.jpg', item_ids=('7244ef2d7394451abfeb57bb33de8adb',)),
        QueryResult(frame_number=7, camera_id='scene-0301', filename='samples/CAM_FRONT/n008-2018-08-31-11-19-57-0400__CAM_FRONT__1535729327912404.jpg', item_ids=('1b2ffdc364c0402dad9decd6290fbb47',)),
        QueryResult(frame_number=7, camera_id='scene-0598', filename='samples/CAM_FRONT/n008-2018-09-18-13-41-50-0400__CAM_FRONT__1537293292662404.jpg', item_ids=('f98255abcaa4448f8e8293516f45c47a',)),
        QueryResult(frame_number=7, camera_id='scene-0658', filename='samples/CAM_FRONT/n008-2018-08-27-11-48-51-0400__CAM_FRONT__1535385155162404.jpg', item_ids=('69c08f8de9eb4af1ade1a6f85f9421fd',)),
        QueryResult(frame_number=7, camera_id='scene-0658', filename='samples/CAM_FRONT/n008-2018-08-27-11-48-51-0400__CAM_FRONT__1535385155162404.jpg', item_ids=('c24e096fcf4c4e55b74892bddc982eaa',)),
        QueryResult(frame_number=7, camera_id='scene-0746', filename='samples/CAM_FRONT/n008-2018-08-30-15-16-55-0400__CAM_FRONT__1535656808162404.jpg', item_ids=('9fff49bd2ddb4719ad65a60d9ae6df63',)),
        QueryResult(frame_number=7, camera_id='scene-0813', filename='samples/CAM_FRONT/n008-2018-09-18-15-26-58-0400__CAM_FRONT__1537299146862404.jpg', item_ids=('7244ef2d7394451abfeb57bb33de8adb',)),
        QueryResult(frame_number=7, camera_id='scene-0816', filename='samples/CAM_FRONT/n008-2018-09-18-15-26-58-0400__CAM_FRONT__1537299239112404.jpg', item_ids=('fad9ff01047349a595412ba5be48ad41',)),
        QueryResult(frame_number=8, camera_id='scene-0301', filename='samples/CAM_FRONT/n008-2018-08-31-11-19-57-0400__CAM_FRONT__1535729328412404.jpg', item_ids=('1b2ffdc364c0402dad9decd6290fbb47',)),
        QueryResult(frame_number=8, camera_id='scene-0541', filename='samples/CAM_FRONT/n008-2018-08-30-15-52-26-0400__CAM_FRONT__1535659404362404.jpg', item_ids=('e8a2ed72b3554c98b18f6b20530a7020',)),
        QueryResult(frame_number=8, camera_id='scene-0598', filename='samples/CAM_FRONT/n008-2018-09-18-13-41-50-0400__CAM_FRONT__1537293293162404.jpg', item_ids=('f98255abcaa4448f8e8293516f45c47a',)),
        QueryResult(frame_number=8, camera_id='scene-0658', filename='samples/CAM_FRONT/n008-2018-08-27-11-48-51-0400__CAM_FRONT__1535385158662404.jpg', item_ids=('c24e096fcf4c4e55b74892bddc982eaa',)),
        QueryResult(frame_number=8, camera_id='scene-0813', filename='samples/CAM_FRONT/n008-2018-09-18-15-26-58-0400__CAM_FRONT__1537299147362404.jpg', item_ids=('7244ef2d7394451abfeb57bb33de8adb',)),
        QueryResult(frame_number=8, camera_id='scene-0816', filename='samples/CAM_FRONT/n008-2018-09-18-15-26-58-0400__CAM_FRONT__1537299240112404.jpg', item_ids=('fad9ff01047349a595412ba5be48ad41',)),
        QueryResult(frame_number=9, camera_id='scene-0301', filename='samples/CAM_FRONT/n008-2018-08-31-11-19-57-0400__CAM_FRONT__1535729328912404.jpg', item_ids=('1b2ffdc364c0402dad9decd6290fbb47',)),
        QueryResult(frame_number=9, camera_id='scene-0541', filename='samples/CAM_FRONT/n008-2018-08-30-15-52-26-0400__CAM_FRONT__1535659404762404.jpg', item_ids=('e8a2ed72b3554c98b18f6b20530a7020',)),
        QueryResult(frame_number=9, camera_id='scene-0598', filename='samples/CAM_FRONT/n008-2018-09-18-13-41-50-0400__CAM_FRONT__1537293293662404.jpg', item_ids=('f98255abcaa4448f8e8293516f45c47a',)),
        QueryResult(frame_number=9, camera_id='scene-0658', filename='samples/CAM_FRONT/n008-2018-08-27-11-48-51-0400__CAM_FRONT__1535385159162404.jpg', item_ids=('c24e096fcf4c4e55b74892bddc982eaa',)),
        QueryResult(frame_number=9, camera_id='scene-0813', filename='samples/CAM_FRONT/n008-2018-09-18-15-26-58-0400__CAM_FRONT__1537299147862404.jpg', item_ids=('7244ef2d7394451abfeb57bb33de8adb',)),
        QueryResult(frame_number=10, camera_id='scene-0301', filename='samples/CAM_FRONT/n008-2018-08-31-11-19-57-0400__CAM_FRONT__1535729329412404.jpg', item_ids=('1b2ffdc364c0402dad9decd6290fbb47',)),
        QueryResult(frame_number=10, camera_id='scene-0541', filename='samples/CAM_FRONT/n008-2018-08-30-15-52-26-0400__CAM_FRONT__1535659405262404.jpg', item_ids=('e8a2ed72b3554c98b18f6b20530a7020',)),
        QueryResult(frame_number=10, camera_id='scene-0658', filename='samples/CAM_FRONT/n008-2018-08-27-11-48-51-0400__CAM_FRONT__1535385159662404.jpg', item_ids=('c24e096fcf4c4e55b74892bddc982eaa',)),
        QueryResult(frame_number=10, camera_id='scene-0813', filename='samples/CAM_FRONT/n008-2018-09-18-15-26-58-0400__CAM_FRONT__1537299148362404.jpg', item_ids=('7244ef2d7394451abfeb57bb33de8adb',)),
        QueryResult(frame_number=11, camera_id='scene-0301', filename='samples/CAM_FRONT/n008-2018-08-31-11-19-57-0400__CAM_FRONT__1535729329912795.jpg', item_ids=('1b2ffdc364c0402dad9decd6290fbb47',)),
        QueryResult(frame_number=11, camera_id='scene-0541', filename='samples/CAM_FRONT/n008-2018-08-30-15-52-26-0400__CAM_FRONT__1535659405762404.jpg', item_ids=('e8a2ed72b3554c98b18f6b20530a7020',)),
        QueryResult(frame_number=11, camera_id='scene-0813', filename='samples/CAM_FRONT/n008-2018-09-18-15-26-58-0400__CAM_FRONT__1537299148862404.jpg', item_ids=('7244ef2d7394451abfeb57bb33de8adb',)),
        QueryResult(frame_number=12, camera_id='scene-0301', filename='samples/CAM_FRONT/n008-2018-08-31-11-19-57-0400__CAM_FRONT__1535729330362404.jpg', item_ids=('1b2ffdc364c0402dad9decd6290fbb47',)),
        QueryResult(frame_number=12, camera_id='scene-0813', filename='samples/CAM_FRONT/n008-2018-09-18-15-26-58-0400__CAM_FRONT__1537299149412404.jpg', item_ids=('7244ef2d7394451abfeb57bb33de8adb',)),
        QueryResult(frame_number=15, camera_id='scene-0557', filename='samples/CAM_FRONT/n008-2018-08-31-11-37-23-0400__CAM_FRONT__1535730293412404.jpg', item_ids=('93447c5bd75b4862995b0a4b12b0459f',)),
    ])