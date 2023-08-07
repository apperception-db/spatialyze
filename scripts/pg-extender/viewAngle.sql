-- `view_point` is the object from which `obj` is being viewed
DROP FUNCTION IF EXISTS viewAngle(geometry, real, geometry);
CREATE OR REPLACE FUNCTION viewAngle(obj_position geometry, view_point_heading real, view_point geometry) RETURNS real AS 
$BODY$
declare clockwise numeric;
declare counterClockwise numeric;
declare azimuth numeric;
-- Note: view_point_heading is counter-clockwise with North being 0, while the result of ST_Azimuth is clockwise with North being 0
BEGIN
    view_point_heading := ((view_point_heading::numeric % 360) + 360) % 360;
    azimuth := (((-ST_Azimuth(view_point, obj_position) * 180 / PI())::numeric % 360) + 360) % 360;
    clockwise := (azimuth - view_point_heading + 360)::numeric % 360;
    counterClockwise := (view_point_heading - azimuth + 360)::numeric % 360;
    IF clockwise < counterClockwise THEN
      RETURN clockwise;
    ELSE 
      RETURN counterClockwise;
    END IF;
END
$BODY$
LANGUAGE 'plpgsql' ;

DROP FUNCTION IF EXISTS viewAngle(tgeompoint, real, geometry, timestamptz);
CREATE OR REPLACE FUNCTION viewAngle(object_trajectory tgeompoint, camera_heading real, camera_location geometry, _time timestamptz) RETURNS real AS
$BODY$
BEGIN
  RETURN viewAngle(valueAtTimestamp(object_trajectory, _time), camera_heading, camera_location);
END
$BODY$
LANGUAGE 'plpgsql' ;

DROP FUNCTION IF EXISTS viewAngle(tgeompoint, tfloat, tgeompoint, timestamptz);
CREATE OR REPLACE FUNCTION viewAngle(object_trajectory tgeompoint, view_obj_headings tfloat, view_obj_location tgeompoint, _time timestamptz) RETURNS real AS
$BODY$
BEGIN
  RETURN viewAngle(valueAtTimestamp(object_trajectory, _time), valueAtTimestamp(view_obj_headings, _time), valueAtTimestamp(view_obj_location, _time));
END
$BODY$
LANGUAGE 'plpgsql' ;