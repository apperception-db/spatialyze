CREATE OR REPLACE FUNCTION roadSegment(segment_type text) RETURNS geometry[] AS
$BODY$
DECLARE
 segment_polygons geometry[];
BEGIN
    IF segment_type = 'lanewithrightlane' THEN
        RETURN (SELECT ARRAY(
            SELECT p.elementPolygon 
            FROM SegmentPolygon as p, LaneSection as ls
            WHERE p.elementId = ls.id AND ls.laneToRight <> 'None'
        ));
    ELSE
        EXECUTE format('SELECT ARRAY(SELECT SegmentPolygon.elementPolygon FROM SegmentPolygon, %I 
        WHERE SegmentPolygon.elementId = %I.id)', segment_type, segment_type) into segment_polygons;
    END IF;
    RETURN segment_polygons;
END
$BODY$
LANGUAGE 'plpgsql';

-- return true, if polygon2 is to the right of polygon1 given the heading of polygon1
CREATE OR REPLACE FUNCTION laneToRight(polygon2 geometry, polygon1 geometry, heading real) RETURNS boolean AS
$BODY$
declare centroid_2 geometry;
declare centroid_1 geometry;
declare subtract_x real;
declare subtract_y real;
BEGIN
    centroid_2 := ST_Centroid(polygon2);
    centroid_1 := ST_Centroid(polygon1);
    subtract_x := ST_X(centroid_2) - ST_X(centroid_1);
    subtract_y := ST_Y(centroid_2) - ST_Y(centroid_1);
    -- return true if (subtract_x, subtract_y) is pointing to the right of 
    -- (COS(PI() * (heading + 90) / 180), SIN(PI() * (heading + 90) / 180))
    RETURN COS(PI() * (heading + 90) / 180) * (-subtract_y) + SIN(PI() * (heading + 90) / 180) * (subtract_x) > 0;
END
$BODY$
LANGUAGE 'plpgsql';