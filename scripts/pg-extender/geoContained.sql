/* return true if a point is contained in any of the geometry in the array*/

/* this first function should already exist in mobilitydb, plz double check**/
DROP FUNCTION IF EXISTS contained(geometry, geometry); 
CREATE OR REPLACE FUNCTION contained(contPoint geometry, geom geometry) RETURNS boolean AS
$BODY$
declare excluded geometry;
BEGIN
  RETURN St_Covers(geom, contPoint);
END
$BODY$
LANGUAGE 'plpgsql' ;

DROP FUNCTION IF EXISTS contained(geometry, geometry[]);
CREATE OR REPLACE FUNCTION contained(contPoint geometry, geoms geometry[]) RETURNS boolean AS
$BODY$
declare geom geometry;
BEGIN
  FOREACH geom IN ARRAY geoms
  LOOP
    IF contained(contPoint, geom) THEN
      RETURN true;
    END IF;  
  END LOOP;
  RETURN false; 
END
$BODY$
LANGUAGE 'plpgsql' ;

-- ------------ USED FOR STBOX TYPES (BOUNDING BOXES) ------------
-- DROP FUNCTION IF EXISTS contained(stbox, geometry); 
-- CREATE OR REPLACE FUNCTION contained(contPoint stbox, geom geometry) RETURNS boolean AS
-- $BODY$
-- BEGIN
--   RETURN contained(contPoint::box3d::geometry, geom);
-- END
-- $BODY$
-- LANGUAGE 'plpgsql' ;

-- DROP FUNCTION IF EXISTS contained(stbox, geometry[]);
-- CREATE OR REPLACE FUNCTION contained(contPoint stbox, geoms geometry[]) RETURNS boolean AS
-- $BODY$
-- BEGIN
--   RETURN contained(contPoint::box3d::geometry, geoms);
-- END
-- $BODY$
-- LANGUAGE 'plpgsql' ;

-- DROP FUNCTION IF EXISTS contained(stbox, geometry[], timestamptz);
-- CREATE OR REPLACE FUNCTION contained(contPoint stbox, geoms geometry[], t timestamptz) RETURNS boolean AS
-- $BODY$
-- BEGIN
--   RETURN contained(contPoint, geoms);
-- END
-- $BODY$
-- LANGUAGE 'plpgsql' ;

DROP FUNCTION IF EXISTS contained(geometry, text);
CREATE OR REPLACE FUNCTION contained(contPoint geometry, segmentType text) RETURNS boolean AS
$BODY$
declare geom geometry;
BEGIN
  RETURN EXISTS(SELECT * FROM SegmentPolygon WHERE ST_Contains(elementPolygon, contPoint) AND segmentType = Any(segmentTypes));
END
$BODY$
LANGUAGE 'plpgsql' ;