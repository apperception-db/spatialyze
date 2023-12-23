DROP FUNCTION IF EXISTS distance(geometry, geometry);
CREATE OR REPLACE FUNCTION distance(a geometry, b geometry) RETURNS float AS
$BODY$
BEGIN
  RETURN ST_Distance(a, b);
END
$BODY$
LANGUAGE 'plpgsql' ;

DROP FUNCTION IF EXISTS distance(geometry, geometry, timestamptz);
CREATE OR REPLACE FUNCTION distance(a geometry, b geometry, t timestamptz) RETURNS float AS
$BODY$
BEGIN
  RETURN distance(a, b);
END
$BODY$
LANGUAGE 'plpgsql' ;

DROP FUNCTION IF EXISTS distance(tgeompoint, geometry, timestamptz);
CREATE OR REPLACE FUNCTION distance(tg tgeompoint, b geometry, t timestamptz) RETURNS float AS
$BODY$
BEGIN
  RETURN distance(valueAtTimestamp(tg, t), b);
END
$BODY$
LANGUAGE 'plpgsql' ;

DROP FUNCTION IF EXISTS distance(geometry, tgeompoint, timestamptz);
CREATE OR REPLACE FUNCTION distance(a geometry, tg tgeompoint, t timestamptz) RETURNS float AS
$BODY$
BEGIN
  RETURN distance(a, valueAtTimestamp(tg, t));
END
$BODY$
LANGUAGE 'plpgsql' ;

DROP FUNCTION IF EXISTS distance(tgeompoint, tgeompoint, timestamptz);
CREATE OR REPLACE FUNCTION distance(a tgeompoint, b tgeompoint, t timestamptz) RETURNS float AS
$BODY$
BEGIN
  RETURN distance(valueAtTimestamp(a, t), valueAtTimestamp(b, t));
END
$BODY$
LANGUAGE 'plpgsql' ;

/* test case
 select get_Y(translations, timestamptz '2021-06-08 07:10:29+00') from Item_Trajectory limit 1;
*/