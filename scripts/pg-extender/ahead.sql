DROP FUNCTION IF EXISTS ahead(geometry, geometry, real);
CREATE OR REPLACE FUNCTION ahead(obj1_loc geometry, obj2_loc geometry, obj2_heading real) RETURNS boolean AS
$BODY$
BEGIN
    -- Since x points to east but angle is 0 for pointing north, the angles need to be added by pi/2
    -- to be in the same coordinate
  RETURN (ST_X(obj1_loc) - ST_X(obj2_loc)) * COS(PI() * (obj2_heading + 90) / 180) + (ST_Y(obj1_loc) - ST_Y(obj2_loc)) * SIN(PI() * (obj2_heading + 90) / 180) > 0 
        AND ABS(ST_X(convertCamera(obj1_loc, obj2_loc, obj2_heading))) < 3;
        -- this condition is supposed to be here (offset by Range(-1, 1) @ 0), but it never satisfies.
END
$BODY$
LANGUAGE 'plpgsql' ;