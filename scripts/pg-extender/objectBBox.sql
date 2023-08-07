DROP FUNCTION IF EXISTS objectBBox(text, timestamptz);
CREATE OR REPLACE FUNCTION objectBBox(id text, t timestamptz) RETURNS stbox AS
$BODY$
BEGIN
  RETURN (SELECT trajBbox FROM General_BBox WHERE itemId = id AND timestamp = t);
END
$BODY$
LANGUAGE 'plpgsql' ;