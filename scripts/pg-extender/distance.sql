DROP FUNCTION IF EXISTS distance(geometry, geometry);
CREATE OR REPLACE FUNCTION distance(a geometry, b geometry) RETURNS float AS
$BODY$
BEGIN
  RETURN ST_Distance(a, b);
END
$BODY$
LANGUAGE 'plpgsql' ;
