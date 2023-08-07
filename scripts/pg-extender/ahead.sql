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

DROP FUNCTION IF EXISTS ahead(geometry, geometry, real, timestamptz);
CREATE OR REPLACE FUNCTION ahead(obj1_loc geometry, obj2_loc geometry, obj2_heading real, t timestamptz) RETURNS boolean AS
$BODY$
BEGIN
  RETURN ahead(obj1_loc, obj2_loc, obj2_heading);
END
$BODY$
LANGUAGE 'plpgsql' ;

DROP FUNCTION IF EXISTS ahead(geometry, tgeompoint, tfloat, timestamptz);
CREATE OR REPLACE FUNCTION ahead(obj1_loc geometry, obj2_loc tgeompoint, obj2_heading tfloat, t timestamptz) RETURNS boolean AS
$BODY$
BEGIN
  RETURN ahead(obj1_loc, valueAtTimestamp(obj2_loc, t), CAST(valueAtTimestamp(object2_heading, t) AS real));
END
$BODY$
LANGUAGE 'plpgsql' ;

DROP FUNCTION IF EXISTS ahead(tgeompoint, geometry, real, timestamptz);
CREATE OR REPLACE FUNCTION ahead(obj1_loc tgeompoint, obj2_loc geometry, obj2_heading real, t timestamptz) RETURNS boolean AS
$BODY$
BEGIN
  RETURN ahead(valueAtTimestamp(obj1_loc, t), obj2_loc, obj2_heading);
END
$BODY$
LANGUAGE 'plpgsql' ;

DROP FUNCTION IF EXISTS ahead(tgeompoint, tgeompoint, tfloat, timestamptz);
CREATE OR REPLACE FUNCTION ahead(obj1_loc tgeompoint, obj2_loc tgeompoint, obj2_heading tfloat, t timestamptz) RETURNS boolean AS
$BODY$
BEGIN
  -- RETURN FALSE;
  RETURN ahead(valueAtTimestamp(obj1_loc, t), valueAtTimestamp(obj2_loc, t), CAST(valueAtTimestamp(obj2_heading, t) AS real));
END
$BODY$
LANGUAGE 'plpgsql' ;