DROP FUNCTION IF EXISTS roadDirection(x real, y real, default_dir real);
CREATE OR REPLACE FUNCTION roadDirection(x real, y real, default_dir real) RETURNS real AS
$BODY$
declare contPolygonElementId text;
declare result real;
BEGIN
     SELECT elementId INTO contPolygonElementId FROM SegmentPolygon WHERE contained(st_point(x, y), elementPolygon)
            AND (SELECT id FROM Lane WHERE id = elementId) IS NOT NULL;
     IF contPolygonElementId IS NOT NULL THEN
        result := (SELECT heading * 180 / PI() FROM segment, st_point(x, y) AS point 
                          WHERE elementId IN (SELECT s.elementId FROM SegmentPolygon AS s WHERE contained(st_point(x, y), s.elementPolygon) AND (SELECT id FROM Lane WHERE id = elementId) IS NOT NULL) 
                                AND ROUND(CAST(heading * 180 / PI() AS numeric), 3) != -45
                          ORDER BY segmentLine <-> point ASC LIMIT 1);
        IF result IS NULL THEN
          -- result := (SELECT heading * 180 / PI() FROM segment, st_point(x, y) AS point 
          --                   WHERE ROUND(CAST(heading * 180 / PI() AS numeric), 3) != -45 
          --                   ORDER BY segmentLine <-> point ASC LIMIT 1 );
          RETURN default_dir;
        END IF;
     ELSE
        -- result := default_dir;
        RETURN default_dir;
     END IF;
     RETURN CAST((result + 360) AS numeric) % 360;
END
$BODY$
LANGUAGE 'plpgsql' ;

DROP FUNCTION IF EXISTS roadDirection(cordPoint geometry, default_dir real);
CREATE OR REPLACE FUNCTION roadDirection(cordPoint geometry, default_dir real) RETURNS real AS
$BODY$
BEGIN
  RETURN roadDirection(Cast(ST_X(ST_Centroid(cordPoint)) AS real), Cast(ST_Y(ST_Centroid(cordPoint)) AS real), default_dir);
END
$BODY$
LANGUAGE 'plpgsql' ;

DROP FUNCTION IF EXISTS roadDirection(cordPoint geometry, _time timestamptz, default_dir real);
CREATE OR REPLACE FUNCTION roadDirection(cordPoint geometry, _time timestamptz, default_dir real) RETURNS real AS
$BODY$
BEGIN
  RETURN roadDirection(cordPoint, default_dir);
END
$BODY$
LANGUAGE 'plpgsql' ;

DROP FUNCTION IF EXISTS roadDirection(trajectory tgeompoint, _time timestamptz, default_dir real);
CREATE OR REPLACE FUNCTION roadDirection(trajectory tgeompoint, _time timestamptz, default_dir real) RETURNS real AS
$BODY$
BEGIN
  RETURN roadDirection(valueAtTimestamp(trajectory, _time), default_dir);
END
$BODY$
LANGUAGE 'plpgsql' ;