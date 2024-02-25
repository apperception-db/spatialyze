/* return true if a point is contained in any of the geometry in the array*/

/* this first function should already exist in mobilitydb, plz double check**/
DROP FUNCTION IF EXISTS containedMargin(geometry, geometry, numeric); 
CREATE OR REPLACE FUNCTION containedMargin(contPoint geometry, geom geometry, margin numeric) RETURNS boolean AS
$BODY$
declare excluded geometry;
BEGIN
  excluded := ST_Difference(contPoint, geom);
  RETURN ST_Area(excluded) / ST_Area(contPoint) < margin; -- or St_Covers(geom, contPoint);
END
$BODY$
LANGUAGE 'plpgsql' ;

-- DROP FUNCTION IF EXISTS containedMargin(geometry, geometry[], numeric);
-- CREATE OR REPLACE FUNCTION containedMargin(contPoint geometry, geoms geometry[], margin numeric) RETURNS boolean AS
-- $BODY$
-- declare geom geometry;
-- BEGIN
--   FOREACH geom IN ARRAY geoms
--   LOOP
--     IF containedMargin(contPoint, geom, margin) THEN
--       RETURN true;
--     END IF;  
--   END LOOP;
--   RETURN false; 
-- END
-- $BODY$
-- LANGUAGE 'plpgsql' ;

-- DROP FUNCTION IF EXISTS containedMargin(tgeompoint, geometry[], numeric, timestamptz);
-- CREATE OR REPLACE FUNCTION containedMargin(contPoint tgeompoint, geoms geometry[], margin numeric, t timestamptz) RETURNS boolean AS
-- $BODY$
-- BEGIN
--   RETURN containedMargin(valueAtTimestamp(contPoint, t), geoms, margin);
-- END
-- $BODY$
-- LANGUAGE 'plpgsql' ;

-- ------------ USED FOR STBOX TYPES (BOUNDING BOXES) ------------
-- DROP FUNCTION IF EXISTS containedMargin(stbox, geometry, numeric); 
-- CREATE OR REPLACE FUNCTION containedMargin(contPoint stbox, geom geometry, margin numeric) RETURNS boolean AS
-- $BODY$
-- BEGIN
--   RETURN containedMargin(contPoint::box3d::geometry, geom, margin);
-- END
-- $BODY$
-- LANGUAGE 'plpgsql' ;

-- DROP FUNCTION IF EXISTS containedMargin(stbox, geometry[], numeric);
-- CREATE OR REPLACE FUNCTION containedMargin(contPoint stbox, geoms geometry[], margin numeric) RETURNS boolean AS
-- $BODY$
-- BEGIN
--   RETURN containedMargin(contPoint::box3d::geometry, geoms, margin);
-- END
-- $BODY$
-- LANGUAGE 'plpgsql' ;

-- DROP FUNCTION IF EXISTS containedMargin(stbox, geometry[], numeric, timestamptz);
-- CREATE OR REPLACE FUNCTION containedMargin(contPoint stbox, geoms geometry[], margin numeric, t timestamptz) RETURNS boolean AS
-- $BODY$
-- BEGIN
--   RETURN containedMargin(contPoint, geoms, margin);
-- END
-- $BODY$
-- LANGUAGE 'plpgsql' ;