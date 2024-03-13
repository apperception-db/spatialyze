DROP FUNCTION IF EXISTS facingRelative(real, real);
CREATE OR REPLACE FUNCTION facingRelative(target_heading real, viewpoint_heading real) RETURNS real AS
$BODY$
BEGIN
  RETURN (((target_heading - viewpoint_heading)::numeric % 360) + 360) % 360;
END
$BODY$
LANGUAGE 'plpgsql' ;
