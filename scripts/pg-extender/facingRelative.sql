DROP FUNCTION IF EXISTS facingRelative(real, real);
CREATE OR REPLACE FUNCTION facingRelative(target_heading real, viewpoint_heading real) RETURNS real AS
$BODY$
BEGIN
  RETURN (((target_heading - viewpoint_heading)::numeric % 360) + 360) % 360;
END
$BODY$
LANGUAGE 'plpgsql' ;


DROP FUNCTION IF EXISTS facingRelative(real, real, timestamptz);
CREATE OR REPLACE FUNCTION facingRelative(target_heading real, viewpoint_heading real, _time timestamptz) RETURNS real AS
$BODY$
BEGIN
  RETURN facingRelative(target_heading, viewpoint_heading);
END
$BODY$
LANGUAGE 'plpgsql' ;


DROP FUNCTION IF EXISTS facingRelative(tfloat, real, timestamptz);
CREATE OR REPLACE FUNCTION facingRelative(target_headings tfloat, viewpoint_heading real, _time timestamptz) RETURNS real AS
$BODY$
BEGIN
  RETURN facingRelative(
    valueAtTimestamp(target_headings, _time)::real,
    viewpoint_heading
  );
END
$BODY$
LANGUAGE 'plpgsql' ;


DROP FUNCTION IF EXISTS facingRelative(tfloat, tfloat, timestamptz);
CREATE OR REPLACE FUNCTION facingRelative(target_headings tfloat, viewpoint_headings tfloat, _time timestamptz) RETURNS real AS
$BODY$
BEGIN
  RETURN facingRelative(
    valueAtTimestamp(target_headings, _time)::real,
    valueAtTimestamp(viewpoint_headings, _time)::real
  );
END
$BODY$
LANGUAGE 'plpgsql' ;