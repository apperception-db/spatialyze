CREATE OR REPLACE FUNCTION angleExcluding(angle real, angle_from real, angle_to real) RETURNS boolean AS
$BODY$
BEGIN
    angle := (((angle::numeric) % 360) + 360) % 360;
    angle_from := (((angle_from::numeric) % 360) + 360) % 360;
    angle_to := (((angle_to::numeric) % 360) + 360) % 360;
    IF angle_from <= angle_to THEN
        RETURN NOT (angle_from < angle AND angle < angle_to);
    ELSE
        RETURN NOT (angle_from < angle OR angle < angle_to);
    END IF;
END
$BODY$
LANGUAGE 'plpgsql' ;