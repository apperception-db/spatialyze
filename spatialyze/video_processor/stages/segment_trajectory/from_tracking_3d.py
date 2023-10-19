import datetime
from typing import NamedTuple

import numpy as np
import postgis
import psycopg2.sql
import shapely.geometry as sg
import shapely.wkb
import torch

from ....database import database
from ...payload import Payload
from ...types import DetectionId, Float2
from ..detection_3d import Detection3D
from ..detection_3d import Metadatum as Detection3DMetadatum
from ..tracking.tracking import Metadatum as TrackingMetadatum
from ..tracking.tracking import Tracking
from . import (
    InvalidSegmentPoint,
    PolygonAndId,
    SegmentPoint,
    SegmentTrajectory,
    SegmentTrajectoryMetadatum,
    ValidSegmentPoint,
)

USEFUL_TYPES = ["lane", "lanegroup", "intersection"]


class FromTracking3D(SegmentTrajectory):
    def __init__(self):
        self.analyze = True
        self.explains = []

    def _run(self, payload: "Payload"):
        d3d: "list[Detection3DMetadatum] | None" = Detection3D.get(payload)
        assert d3d is not None

        tracking: "list[TrackingMetadatum] | None" = Tracking.get(payload)
        assert tracking is not None

        class_map: "list[str] | None" = d3d[0].class_map
        assert class_map is not None

        # Index detections using their detection id
        detection_map: "dict[DetectionId, tuple[int, int]]" = dict()
        for fidx, (_, names, dids) in enumerate(d3d):
            for oidx, did in enumerate(dids):
                assert did not in detection_map
                detection_map[did] = (fidx, oidx)

        object_map: "dict[int, dict[DetectionId, torch.Tensor]]" = dict()
        for fidx, frame in enumerate(tracking):
            for tracking_result in frame:
                did = tracking_result.detection_id
                oid = tracking_result.object_id
                if oid not in object_map:
                    object_map[oid] = {}
                if did in object_map[oid]:
                    continue
                fidx, oidx = detection_map[did]
                detections, *_ = d3d[fidx]
                object_map[oid][did] = detections[oidx]

        # Index object trajectories using their object id
        # object_map: "dict[int, list[Tracking3DResult]]" = dict()
        # for frame in t3d:
        #     for oid, t in frame.items():
        #         if oid not in object_map:
        #             object_map[oid] = []

        #         object_map[oid].append(t)

        # Create a list of detection points with each of its corresponding direction
        points: "list[tuple[tuple[DetectionId, torch.Tensor], tuple[float, float] | None]]" = []
        for traj_dict in object_map.values():
            traj = [*traj_dict.items()]
            traj.sort(key=lambda t: t[0].frame_idx)

            if len(traj) <= 1:
                points.extend((t, None) for t in traj)
                continue

            # First and last points' direction
            points.append((traj[0], _get_direction_2d(traj[0], traj[1])))
            points.append((traj[-1], _get_direction_2d(traj[-2], traj[-1])))

            # All other points' direction
            for prv, cur, nxt in zip(traj[:-2], traj[1:-1], traj[2:]):
                points.append((cur, _get_direction_2d(prv, nxt)))

        locations = set(f.location for f in payload.video._camera_configs)
        assert len(locations) == 1, locations

        location = [*locations][0]

        # Map a segment to each detection
        # Note: Some detection might be missing due to not having any segment mapped
        segments = map_points_and_directions_to_segment(
            points, location, payload.video.videofile, self.explains
        )

        # Index segments using their detection id
        segment_map: "dict[DetectionId, SegmentMapping]" = {}
        for segment in segments:
            did = DetectionId(*segment[:2])
            if did not in segment_map:
                # assert did not in segment_map
                segment_map[did] = segment

        object_id_to_segmnt_map: "dict[int, list[SegmentPoint]]" = {}
        output: "list[SegmentTrajectoryMetadatum]" = [dict() for _ in range(len(payload.video))]
        for oid, obj in object_map.items():
            segment_trajectory: "list[SegmentPoint]" = []
            object_id_to_segmnt_map[oid] = segment_trajectory

            for did, det in obj.items():
                # did = det.detection_id
                timestamp = payload.video.interpolated_frames[did.frame_idx].timestamp
                args = did, timestamp, det, oid, class_map
                if did in segment_map:
                    # Detection that can be mapped to a segment
                    segment = segment_map[did]
                    _fid, _oid, polygonid, polygon, segmentid, types, line, heading = segment
                    assert did.frame_idx == _fid
                    assert did.obj_order == _oid

                    polygon = shapely.wkb.loads(polygon.to_ewkb(), hex=True)
                    assert isinstance(polygon, sg.Polygon)

                    type_ = next((t for t in types if t in USEFUL_TYPES), types[-1])

                    segment_point = valid_segment_point(
                        *args, type_, line, heading, polygonid, polygon
                    )
                else:
                    # Detection that cannot be mapped to any segment
                    segment_point = invalid_segment_point(*args)

                segment_trajectory.append(segment_point)

                metadatum = output[did.frame_idx]
                if oid in metadatum:
                    assert metadatum[oid].detection_id == segment_point.detection_id
                    if metadatum[oid].timestamp > segment_point.timestamp:
                        metadatum[oid] = segment_point
                metadatum[oid] = segment_point

            for prv, nxt in zip(segment_trajectory[:-1], segment_trajectory[1:]):
                prv.next = nxt
                nxt.prev = prv

        return None, {self.classname(): output}


def invalid_segment_point(
    did: "DetectionId",
    timestamp: "datetime.datetime",
    det: "torch.Tensor",
    oid: "int",
    class_map: "list[str]",
):
    x, y, z = map(float, ((det[6:9] + det[9:12]) / 2).tolist())
    return InvalidSegmentPoint(
        did,
        (x, y, z),
        timestamp,
        oid,
        class_map[int(det[5])],
    )


def valid_segment_point(
    did: "DetectionId",
    timestamp: "datetime.datetime",
    det: "torch.Tensor",
    oid: "int",
    class_map: "list[str]",
    segmenttype: "str",
    segmentline: "postgis.LineString",
    segmentheading: "float",
    polygonid: "str",
    shapely_polygon: "sg.Polygon",
):
    x, y, z = map(float, ((det[6:9] + det[9:12]) / 2).tolist())
    return ValidSegmentPoint(
        did,
        (x, y, z),
        timestamp,
        segmenttype,
        segmentline,
        segmentheading,
        # A place-holder for Polygon that only contain polygon id and polygon
        PolygonAndId(polygonid, shapely_polygon),
        oid,
        class_map[int(det[5])],
    )


def _get_direction_2d(
    p1: "tuple[DetectionId, torch.Tensor]", p2: "tuple[DetectionId, torch.Tensor]"
) -> "Float2":
    _p1 = (p1[1][6:9] + p1[1][9:12]) / 2
    _p2 = (p2[1][6:9] + p2[1][9:12]) / 2
    diff = (_p2 - _p1)[:2].cpu()
    udiff = diff / np.linalg.norm(diff)
    x, y = map(float, udiff.numpy())
    return x, y


class SegmentMapping(NamedTuple):
    fid: "int"
    oid: "int"
    elementid: "str"
    polygon: "postgis.Polygon"
    segmentid: "int"
    segmenttypes: "list[str]"
    line: "postgis.LineString"
    heading: "float"


# TODO: should we try to map points to closest segment instead of just ignoring them?


def map_points_and_directions_to_segment(
    annotations: "list[tuple[tuple[DetectionId, torch.Tensor], tuple[float, float] | None]]",
    # annotations: "list[tuple[Tracking3DResult, tuple[float, float] | None]]",
    location: "str",
    videofile: "str",
    explains: "list[dict]",
) -> "list[SegmentMapping]":
    if len(annotations) == 0:
        return []

    frame_indices = [a[0].frame_idx for a, _ in annotations]
    object_indices = [a[0].obj_order for a, _ in annotations]
    points = [(a[1][6:9] + a[1][9:12]) / 2 for a, _ in annotations]
    txs = [float(p[0].item()) for p in points]
    tys = [float(p[1].item()) for p in points]
    dxs = [d and d[0] for _, d in annotations]
    dys = [d and d[1] for _, d in annotations]

    _point = psycopg2.sql.SQL(
        "UNNEST({fid}, {oid}, {tx}, {ty}, {dx}::double precision[], {dy}::double precision[]) AS _point (fid, oid, tx, ty, dx, dy)"
    ).format(
        fid=psycopg2.sql.Literal(frame_indices),
        oid=psycopg2.sql.Literal(object_indices),
        tx=psycopg2.sql.Literal(txs),
        ty=psycopg2.sql.Literal(tys),
        dx=psycopg2.sql.Literal(dxs),
        dy=psycopg2.sql.Literal(dys),
        # fields=psycopg2.sql.SQL(',').join(map(psycopg2.sql.Literal, [frame_indices, object_indices, txs, tys, dxs, dys]))
    )

    helper = psycopg2.sql.SQL(
        """
    SET client_min_messages TO WARNING;
    DROP FUNCTION IF EXISTS _angle(double precision);
    CREATE OR REPLACE FUNCTION _angle(a double precision) RETURNS double precision AS
    $BODY$
    BEGIN
        RETURN ((a::decimal % 360) + 360) % 360;
    END
    $BODY$
    LANGUAGE 'plpgsql';
    """
    )

    query = psycopg2.sql.SQL(
        """
    WITH
    Point AS (SELECT * FROM {_point}),
    AvailablePolygon AS (
        SELECT *
        FROM SegmentPolygon
        WHERE location = {location}
        AND (SegmentPolygon.__RoadType__intersection__
        OR SegmentPolygon.__RoadType__lane__
        OR SegmentPolygon.__RoadType__lanegroup__
        OR SegmentPolygon.__RoadType__lanesection__)
    ),
    _SegmentWithDirection AS (
        SELECT
            *,
            ST_X(endPoint) - ST_X(startPoint) AS _x,
            ST_Y(endPoint) - ST_Y(startPoint) AS _y
        FROM Segment
    ),
    SegmentWithDirection AS (
        SELECT
            *,
            (_x / SQRT(POWER(_x, 2) + POWER(_y, 2))) AS dx,
            (_y / SQRT(POWER(_x, 2) + POWER(_y, 2))) AS dy
        FROM _SegmentWithDirection
        WHERE
            _x <> 0 OR _y <> 0
    ),
    MinPolygon AS (
        SELECT fid, oid, MIN(ST_Area(Polygon.elementPolygon)) as size
        FROM Point AS p
        JOIN AvailablePolygon AS Polygon
            ON ST_Contains(Polygon.elementPolygon, ST_Point(p.tx, p.ty))
        GROUP BY fid, oid
    ),
    MinPolygonId AS (
        SELECT fid, oid, MIN(elementId) as elementId
        FROM Point AS p
        JOIN MinPolygon USING (fid, oid)
        JOIN AvailablePolygon as Polygon
            ON ST_Contains(Polygon.elementPolygon, ST_Point(p.tx, p.ty))
            AND ST_Area(Polygon.elementPolygon) = MinPolygon.size
        GROUP BY fid, oid
    ),
    PointPolygonSegment AS (
        SELECT
            *,
            ST_Distance(ST_Point(tx, ty), ST_MakeLine(startPoint, endPoint)) AS distance,
            CASE
                WHEN p.dx IS NULL THEN 0
                WHEN p.dy IS NULL THEN 0
                ELSE _angle(ACOS((p.dx * sd.dx) + (p.dy * sd.dy)) * 180 / PI())
            END AS anglediff
        FROM Point AS p
        JOIN MinPolygonId USING (fid, oid)
        JOIN AvailablePolygon USING (elementId)
        JOIN SegmentWithDirection AS sd USING (elementId)
        WHERE
            AvailablePolygon.__RoadType__intersection__
            OR
            p.dx IS NULL
            OR
            p.dy IS NULL
            OR
            _angle(ACOS((p.dx * sd.dx) + (p.dy * sd.dy)) * 180 / PI()) < 90
            OR
            _angle(ACOS((p.dx * sd.dx) + (p.dy * sd.dy)) * 180 / PI()) > 270
    ),
    MinDis as (
        SELECT fid, oid, MIN(distance) as mindistance
        FROM PointPolygonSegment
        GROUP BY fid, oid
    ),
    MinDisMinAngle as (
        SELECT fid, oid, MIN(LEAST(pps.anglediff, 360-pps.anglediff)) as minangle
        FROM PointPolygonSegment AS pps
        JOIN MinDis USING (fid, oid)
        WHERE pps.distance = MinDis.mindistance
        GROUP BY fid, oid
    )

    SELECT fid, oid, elementid, elementpolygon, segmentid, segmenttypes, segmentline, heading
    FROM PointPolygonSegment
    JOIN MinDis USING (fid, oid)
    JOIN MinDisMinAngle USING (fid, oid)
    WHERE PointPolygonSegment.distance = MinDis.mindistance
        AND PointPolygonSegment.anglediff = MinDisMinAngle.minangle
    """
    ).format(_point=_point, location=psycopg2.sql.Literal(location))

    # explain = psycopg2.sql.SQL(" EXPLAIN (ANALYZE, COSTS, VERBOSE, BUFFERS, FORMAT JSON) ")
    # explains.append({
    #     'name': videofile,
    #     'analyze': database.execute(helper + explain + query)[0][0][0]
    # })

    result = database.execute(helper + query)
    return list(map(SegmentMapping._make, result))
