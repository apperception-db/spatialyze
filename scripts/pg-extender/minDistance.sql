DROP FUNCTION IF EXISTS minDistance(geometry, geometry[]);
CREATE OR REPLACE FUNCTION minDistance(p geometry, geoms geometry[]) RETURNS real AS
$BODY$
declare geom geometry;
declare min_dis real;
BEGIN
    RETURN (
        SELECT MIN(ST_Distance(p, UNNEST))
        FROM UNNEST(geoms)
    );
END
$BODY$
LANGUAGE 'plpgsql' ;

DROP FUNCTION IF EXISTS minDistance(geometry, text);
CREATE OR REPLACE FUNCTION minDistance(p geometry, segment_type text) RETURNS real AS
$BODY$
BEGIN
    RETURN (
        SELECT MIN(ST_Distance(p, elementPolygon))
        FROM SegmentPolygon
        WHERE segment_type = Any(segmentTypes)
    );
END
$BODY$
LANGUAGE 'plpgsql' ;