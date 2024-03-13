DROP FUNCTION IF EXISTS ConvertCamera(geometry, geometry, real);
CREATE OR REPLACE FUNCTION ConvertCamera(objPoint geometry, camPoint geometry, camHeading real) RETURNS geometry AS
$BODY$
DECLARE subtract_x real;
DECLARE subtract_y real;
DECLARE subtract_mag real;
-- For explanation of math behind this function, see https://github.com/apperception-db/apperception/issues/102.
--    Note: The above github issue was made when camHeading was clockwise, which it no longer is, and thus, camHeading
--          is now negated in the function as below.
BEGIN
  subtract_x := ST_X(ST_Centroid(objPoint)) - ST_X(ST_Centroid(camPoint));
  subtract_y := ST_Y(ST_Centroid(objPoint)) - ST_Y(ST_Centroid(camPoint));
  subtract_mag := SQRT(POWER(subtract_x, 2) + POWER(subtract_y, 2));
  RETURN ST_MakePoint(subtract_mag * COS(PI() * (-camHeading) / 180 + ATAN2(subtract_y, subtract_x)),
                      subtract_mag * SIN(PI() * (-camHeading) / 180 + ATAN2(subtract_y, subtract_x)));
END
$BODY$
LANGUAGE 'plpgsql';
