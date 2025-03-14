import os
import pickle
import pytest
import json
import duckdb
import time

from spatialyze.predicate import *
from spatialyze.utils import F, ingest_road

from spatialyze.video_processor.stages.in_view.in_view import FindRoadTypes, InViewPredicate, KeepOnlyRoadTypePredicates, NormalizeInversionAndFlattenRoadTypePredicates, PushInversionInForRoadTypePredicates, InView, get_views, roadtype, overlap_or, overlap_each
from spatialyze.video_processor.pipeline import Pipeline
from spatialyze.video_processor.payload import Payload
from spatialyze.video_processor.video import Video
from spatialyze.video_processor.camera_config import camera_config
from spatialyze.database import Database, database

import shapely.wkb
import shapely.wkt


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

@pytest.mark.parametrize("fn, sqls", [
    # Propagate Boolean
    (o.type & False, ['False']),
    (o.type | True, ['True']),

    (o.type | (~(o.id & False)), ['True']),
    (o.type & (~(o.id | True)), ['False']),

    (o.type & (~((o.id | True) & True)), ['False']),
    (o.type | (~((o.id & False) | False)), ['True']),

    # General
    (o.type & True, ['ignore_roadtype()', None, None]),
    (o.type & True & F.contains('intersection', o), [
        '(ignore_roadtype() AND is_roadtype(intersection))',
        None,
        'is_roadtype(intersection)',
        f"('intersection' in {RT})",
        {'intersection'}
    ]),
    (arr(), ['ignore_roadtype()', None, None]),
    (~(F.contains('intersection', o) & F.contains('lane', o2)), ['(NOT (is_roadtype(intersection) AND is_roadtype(lane)))', '(is_other_roadtype(intersection) OR is_other_roadtype(lane))', '(is_roadtype(intersection) OR is_roadtype(lane) OR is_roadtype(lanegroup) OR is_roadtype(lanesection) OR is_roadtype(road) OR is_roadtype(roadsection))']),
    (~(F.contains('intersection', o) | F.contains('lane', o2)), ['(NOT (is_roadtype(intersection) OR is_roadtype(lane)))', '(is_other_roadtype(intersection) AND is_other_roadtype(lane))', '((is_roadtype(lanegroup) OR is_roadtype(lane) OR is_roadtype(lanesection)) AND (is_roadtype(lanegroup) OR is_roadtype(road) OR is_roadtype(roadsection) OR is_roadtype(intersection)))']),
    (~(~F.contains('intersection', o) | F.contains('lane', o2)), ['(NOT ((NOT is_roadtype(intersection)) OR is_roadtype(lane)))', '(is_roadtype(intersection) AND is_other_roadtype(lane))', 'is_roadtype(intersection)']),
    (F.contains(F.road_segment('intersection'), o), ['is_roadtype(intersection)', None, 'is_roadtype(intersection)', f"('intersection' in {RT})", {'intersection'}]),

    # Real Queries
    ((((o1.type == 'car') | (o1.type == 'truck')) &
        F.heading_diff(c.ego, F.road_direction(c.ego), between=[-15, 15]) &
        (F.distance(c.ego, o1) < 50) &
        F.contains('intersection', [o1]) &
        F.heading_diff(o1, c.ego, between=[135, 225]) &
        (F.min_distance(c.ego, 'intersection') < 10)), [
        '((ignore_roadtype() OR ignore_roadtype()) AND ignore_roadtype() AND ignore_roadtype() AND is_roadtype(intersection) AND ignore_roadtype() AND ignore_roadtype())',
        None,
        'is_roadtype(intersection)',
        f"('intersection' in {RT})",
        {'intersection'}
    ]),
    (((((o1.type == 'car') | (o1.type == 'truck')) &
        F.heading_diff(c.ego, F.road_direction(c.ego), between=[-15, 15]) &
        (F.distance(c.ego, o1) < 50) &
        F.heading_diff(o1, c.ego, between=[135, 225]) &
        (F.min_distance(c.ego, 'intersection') < 10)) |
        F.contains('intersection', [o1])), [
        '(((ignore_roadtype() OR ignore_roadtype()) AND ignore_roadtype() AND ignore_roadtype() AND ignore_roadtype() AND ignore_roadtype()) OR is_roadtype(intersection))',
        None,
        'ignore_roadtype()',
    ]),
    ((((o1.type == 'car') | (o1.type == 'truck')) &
        F.contains('intersection', [o1]) &
        F.contains('lanesection', [o1]) &
        (F.min_distance(c.ego, 'intersection') < 10)), [
        '((ignore_roadtype() OR ignore_roadtype()) AND is_roadtype(intersection) AND is_roadtype(lanesection) AND ignore_roadtype())',
        None,
        '(is_roadtype(intersection) AND is_roadtype(lanesection))',
        f"(('intersection' in {RT}) and ('lanesection' in {RT}))",
        {'intersection', 'lanesection'}
    ]),
    ((((o1.type == 'car') | (o1.type == 'truck')) &
        F.contains('intersection', [o1]) &
        ~F.contains('lanesection', [o1]) &
        (F.min_distance(c.ego, 'intersection') < 10)), [
        '((ignore_roadtype() OR ignore_roadtype()) AND is_roadtype(intersection) AND (NOT is_roadtype(lanesection)) AND ignore_roadtype())',
        '((ignore_roadtype() OR ignore_roadtype()) AND is_roadtype(intersection) AND is_other_roadtype(lanesection) AND ignore_roadtype())',
        'is_roadtype(intersection)',
        f"('intersection' in {RT})",
        {'intersection'}
    ]),
])
def test_predicates(fn, sqls):
    node = KeepOnlyRoadTypePredicates()(fn)
    assert gen(node) == sqls[0], node
    node1 = None
    node2 = None
    
    if len(sqls) > 1:
        sql = sqls[1]
        node1 = PushInversionInForRoadTypePredicates()(node)
        assert gen(node1) == (gen(node) if sql is None else sql), node1
    
    if len(sqls) > 2:
        sql = sqls[2]
        assert node1 is not None
        node2 = NormalizeInversionAndFlattenRoadTypePredicates()(node1)
        assert gen(node2) == (gen(node1) if sql is None else sql), node2
    
    if len(sqls) > 3:
        assert isinstance(sqls[3], str), sqls[3]
        assert isinstance(sqls[4], set), sqls[4]
        assert node2 is not None

        predicate_str = InViewPredicate(RT)(node2)
        assert predicate_str == sqls[3], predicate_str

        roadtypes = FindRoadTypes()(node2)
        assert roadtypes == sqls[4], roadtypes


def test_repr():
    assert repr(InView(10, roadtypes=['intersection'])) == "InView(distance=10, roadtype=['intersection'], predicate=False)"


# TODO: add these predicates

# @pytest.mark.parametrize("fn, sql", [
#     (o.c1 + c.c1, "true"),
#     (o.c1 == c.c1, "true"),
#     (o.c1 < c.c1, "true"),
#     (o.c1 != c.c1, "true"),

#     (lit(3), "3"),
#     (lit('test', False), "test"),

#     (c0.c1, "true"),
#     (cast(c0.c1, 'real'), "true"),

#     (-o.c1, "(-t0.c1)"),
#     (~o.c1, "(NOT t0.c1)"),
#     (~F.contains('intersection', o.c1), "(NOT SegmentPolygon.__RoadType__intersection__)"),
#     (~F.contains('intersection', o.c1), "(NOT SegmentPolygon.__RoadType__intersection__)"),
#     (o.c1 & ~F.contains('intersection', o.c1) & F.contains('intersection', o.c1), "(true AND true AND SegmentPolygon.__RoadType__intersection__)"),
#     (o.c1 | ~F.contains('intersection', o.c1) | F.contains('intersection', o.c1), "(true OR true OR SegmentPolygon.__RoadType__intersection__)"),
#     (o.c1 @ c.timestamp, "valueAtTimestamp(t0.c1,timestamp)"),
#     (c.timestamp @ 1, "valueAtTimestamp(timestamp,1)"),
#     ([o.c1, o.c2] @ c.timestamp, "ARRAY[valueAtTimestamp(t0.c1,timestamp),valueAtTimestamp(t0.c2,timestamp)]"),
#     (o.bbox @ c.timestamp, "objectBBox(t0.itemId,timestamp)"),
# ])
# def test_simple_ops(fn, sql):

#     assert gen(normalize(fn)) == sql


# @pytest.mark.parametrize("fn, sql", [
#     ((o.c1 + c.c1) - c.c2 + o.c2 * c.c3 / o.c3, "(((t0.c1+c1)-c2)+((t0.c2*c3)/t0.c3))"),
#     ((o.c1 == c.c1) & ((o.c2 < c.c2) | (o.c3 == c.c3)), "((t0.c1=c1) AND ((t0.c2<c2) OR (t0.c3=c3)))"),
# ])
# def test_nested(fn, sql):
#     assert gen(normalize(fn)) == sql


# @pytest.mark.parametrize("fn, tables, camera", [
#     (o.c1 & o1.c2 & c.c3, {0, 1}, True),
#     ((o.c1 + c.c1) - c.c2 + o.c2 * c.c3 / o.c3, {0}, True),
#     ((o.c1) + o1.c2 / o.c3, {0, 1}, False),
#     ((o.c1) + c.c2 / o.c3, {0}, True),
# ])
# def test_find_all_tables(fn, tables, camera):
#     assert FindAllTablesVisitor()(normalize(fn)) == (tables, camera)

OUTPUT_DIR = './data/pipeline/test-results'
VIDEO_DIR =  './data/pipeline/videos'

def test_detection_2d():
    files = os.listdir(VIDEO_DIR)

    ingest_road(database, './data/scenic/road-network/boston-seaport')

    with open(os.path.join(VIDEO_DIR, 'frames.pkl'), 'rb') as f:
        videos = pickle.load(f)
    
    for distance in [10, 20, 30, 40, 50]:
        pipeline1 = Pipeline([InView(distance, roadtypes='intersection')])
        pipeline2 = Pipeline([InView(distance, predicate=(
            ((o1.type == 'car') | (o1.type == 'truck')) &
            F.contains('intersection', [o1]) &
            ~F.contains('lanesection', [o1]) &
            (F.min_distance(c.ego, 'intersection') < 10))
        )])

        for name, video in videos.items():
            if video['filename'] not in files:
                continue
            
            frames = Video(
                os.path.join(VIDEO_DIR, video["filename"]),
                [camera_config(*f) for f in video["frames"]],
            )

            output1 = pipeline1.run(Payload(frames))
            output2 = pipeline2.run(Payload(frames))

            assert output1.keep == output2.keep, (name, output1.keep, output2.keep)

            keeparray = [1 if keep else 0 for keep in output1.keep]
            # with open(os.path.join(OUTPUT_DIR, f'InView_keep_{name}_{distance}.json'), 'w') as f:
            #     json.dump(keeparray, f)

            with open(os.path.join(OUTPUT_DIR, f'InView_keep_{name}_{distance}.json'), 'r') as f:
                keeparraygt = json.load(f)
            
            assert keeparray == keeparraygt, (name, keeparray, keeparraygt)


def test_get_views():
    files = os.listdir(VIDEO_DIR)
    dbfile = '/tmp/__spatialyze__test_get_views.duckdb'
    if os.path.exists(dbfile):
        os.remove(dbfile)
    db = Database(duckdb.connect(dbfile))
    start = time.time()
    ingest_road(db, './data/scenic/road-network/boston-seaport')
    end = time.time()
    print(f"ingest_road: {end - start}")

    with open(os.path.join(VIDEO_DIR, 'frames.pkl'), 'rb') as f:
        videos = pickle.load(f)
    
    for distance in [10, 20, 30, 40, 50]:
        for name, video in videos.items():
            if video['filename'] not in files:
                continue

            frames = Video(
                os.path.join(VIDEO_DIR, video["filename"]),
                [camera_config(*f) for f in video["frames"]],
            )
            indices, view_areas = get_views(frames, distance)
            start = time.time()
            res = db.execute(
                "SELECT index, ST_AsText(ST_ReducePrecision(points, 0.0001)) "
                "FROM (SELECT ST_GeomFromWKB(UNNEST(?)), UNNEST(?)) AS ViewArea(points, index) ",
                (view_areas, indices)
            )
            end = time.time()
            print(f"get_views db {distance}: {end - start}")
            # with open(os.path.join(OUTPUT_DIR, f'InView_get_views_db_{name}_{distance}.json'), 'w') as f:
            #     json.dump(res, f, indent=2)
            with open(os.path.join(OUTPUT_DIR, f'InView_get_views_db_{name}_{distance}.json'), 'r') as f:
                gt_res = json.load(f)
                assert (
                    [(i, shapely.wkt.loads(m)) for i, m in res]
                    ==
                    [(i, shapely.wkt.loads(m)) for i, m in gt_res]
                ), (name, res, gt_res)

            for rt in [['intersection'], ['lane'], ['intersection', 'lane']]:
                start = time.time()
                results = overlap_or(db, indices, view_areas, rt)
                end = time.time()
                print(f"overlap_or {distance} {rt}", end - start)
                results = [r[0] for r in results]
                # with open(os.path.join(OUTPUT_DIR, f'InView_get_views_db_{name}_{distance}_{"_".join(rt)}.json'), 'w') as f:
                #     json.dump(results, f, indent=2)
                with open(os.path.join(OUTPUT_DIR, f'InView_get_views_db_{name}_{distance}_{"_".join(rt)}.json'), 'r') as f:
                    gt_res = json.load(f)
                    assert set(json.loads(json.dumps(results))) == set(gt_res), (name, results, gt_res)

                start = time.time()
                results = overlap_each(db, indices, view_areas, rt)
                end = time.time()
                print(f"overlap_each {distance} {rt}", end - start)
                # with open(os.path.join(OUTPUT_DIR, f'InView_get_views_db_{name}_{distance}_2_{"_".join(rt)}.json'), 'w') as f:
                #     json.dump(results, f, indent=2)
                with open(os.path.join(OUTPUT_DIR, f'InView_get_views_db_{name}_{distance}_2_{"_".join(rt)}.json'), 'r') as f:
                    gt_res = [tuple(t) for t in json.load(f)]
                    assert set(tuple(t) for t in results) == set(gt_res), (name, results, gt_res)

            view_areas_ = [[[round(p.x, 4), round(p.y, 4)] for p in shapely.wkb.loads(va)] for va in view_areas]
            # with open(os.path.join(OUTPUT_DIR, f'InView_get_views_{name}_{distance}.json'), 'w') as f:
            #     json.dump([indices, view_areas_], f, indent=2)
            with open(os.path.join(OUTPUT_DIR, f'InView_get_views_{name}_{distance}.json'), 'r') as f:
                gt_indices, gt_view_areas = json.load(f)
                assert indices == gt_indices, (name, indices, gt_indices)
                assert view_areas_ == gt_view_areas, (name, view_areas_, gt_view_areas)
            