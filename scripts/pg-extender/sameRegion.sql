DROP FUNCTION IF EXISTS sameRegion(text, geometry, geometry);
CREATE OR REPLACE FUNCTION sameRegion(segment_type text, traj1 geometry, traj2 geometry) RETURNS boolean AS
$BODY$
DECLARE
declare result text;
BEGIN
    -- EXECUTE format('SELECT ARRAY(SELECT SegmentPolygon.elementPolygon FROM SegmentPolygon, %I 
    -- WHERE SegmentPolygon.elementId = %I.id)', segment_type, segment_type) into segment_polygons;
    -- RETURN segment_polygons;
    EXECUTE format('SELECT SegmentPolygon.elementId FROM SegmentPolygon, %I 
                        WHERE SegmentPolygon.elementId = %I.id
                        AND contained(geometry %L, SegmentPolygon.elementPolygon) AND contained(geometry %L, SegmentPolygon.elementPolygon);', 
                    segment_type, segment_type, traj1, traj2) into result;
    IF result IS NOT NULL THEN
        return true;
    ELSE
        return false;
    END IF;
END
$BODY$
LANGUAGE 'plpgsql' ;

DROP FUNCTION IF EXISTS sameRegion(text, tgeompoint, geometry, timestamptz);
CREATE OR REPLACE FUNCTION sameRegion(segment_type text, traj1 tgeompoint, traj2 geometry, t timestamptz) RETURNS boolean AS
$BODY$
BEGIN
  RETURN sameRegion(segment_type, valueAtTimestamp(traj1, t), traj2);
END
$BODY$
LANGUAGE 'plpgsql' ;

DROP FUNCTION IF EXISTS sameRegion(text, geometry, tgeompoint, timestamptz);
CREATE OR REPLACE FUNCTION sameRegion(segment_type text, traj1 geometry, traj2 tgeompoint, t timestamptz) RETURNS boolean AS
$BODY$
BEGIN
  RETURN sameRegion(segment_type, traj1, valueAtTimestamp(traj2, t));
END
$BODY$
LANGUAGE 'plpgsql' ;

DROP FUNCTION IF EXISTS sameRegion(text, tgeompoint, tgeompoint, timestamptz);
CREATE OR REPLACE FUNCTION sameRegion(segment_type text, traj1 tgeompoint, traj2 tgeompoint, t timestamptz) RETURNS boolean AS
$BODY$
BEGIN
  RETURN sameRegion(segment_type, valueAtTimestamp(traj1, t), valueAtTimestamp(traj2, t));
END
$BODY$
LANGUAGE 'plpgsql' ;
