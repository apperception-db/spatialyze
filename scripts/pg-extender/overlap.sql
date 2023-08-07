DROP FUNCTION IF EXISTS overlap(stbox, stbox);
CREATE OR REPLACE FUNCTION overlap(bbox1 stbox, bbox2 stbox) RETURNS boolean AS
$BODY$
BEGIN
  RETURN bbox1 && bbox2;
END
$BODY$
LANGUAGE 'plpgsql' ;