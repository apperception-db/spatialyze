-- Checks whether a segment of the specified type is in view within some distance and some view angle
DROP FUNCTION IF EXISTS inView(text, real, geometry, real, real);
CREATE OR REPLACE FUNCTION inView(segment_type text, view_point_heading real, view_point geometry, max_distance real, view_angle real) RETURNS boolean AS 
$BODY$
declare leftViewLine geometry;
declare rightViewLine geometry;
-- Note: view_point_heading is counter-clockwise with North being 0, while the result of ST_Azimuth is clockwise with North being 0
BEGIN
    leftViewLine := viewAngleLine(view_point_heading, view_point, max_distance, -view_angle);
    rightViewLine := viewAngleLine(view_point_heading, view_point, max_distance, view_angle);
    RETURN EXISTS(SELECT * FROM SegmentPolygon 
                        WHERE segment_type = Any(segmentTypes) 
                          AND ST_Distance(view_point, elementPolygon) < max_distance 
                          AND (viewAngle(ST_Centroid(elementPolygon) , view_point_heading, view_point) < view_angle
                               OR ST_Intersects(elementPolygon, leftViewLine)
                               OR ST_Intersects(elementPolygon, rightViewLine)
                              )
                  );
END
$BODY$
LANGUAGE 'plpgsql' ;


DROP FUNCTION IF EXISTS viewAngleLine(real, geometry, real, real);
CREATE OR REPLACE FUNCTION viewAngleLine(view_point_heading real, view_point geometry, max_distance real, view_angle real) RETURNS geometry AS
$BODY$
BEGIN 
  RETURN ST_Translate(ST_Rotate(ST_MakeLine(ST_MakePoint(0, 0), ST_MakePoint(0, max_distance)),
                                            radians(view_point_heading + view_angle)), 
                                            ST_X(view_point), ST_Y(view_point));
END
$BODY$
LANGUAGE 'plpgsql' ;
