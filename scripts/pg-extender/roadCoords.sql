DROP FUNCTION IF EXISTS roadCoords(x real, y real);
CREATE OR REPLACE FUNCTION roadCoords(x real, y real) RETURNS real[] AS
$BODY$
BEGIN
     RETURN (SELECT ARRAY[ST_X(startPoint), ST_Y(startPoint), ST_X(endPoint), ST_Y(endPoint)] 
                FROM RoadSection, Segment, st_point(x, y) AS point 
                WHERE RoadSection.id = Segment.elementId
                ORDER BY segmentLine <-> point ASC LIMIT 1 );
    --  RETURN (SELECT heading * 180 / PI() FROM segment, st_point(x, y) AS POINT, 
    --                                    st_distance(st_makeline(startPoint, endPoint), point) as dis
    --         ORDER BY dis ASC
    --         LIMIT 1);
END
$BODY$
LANGUAGE 'plpgsql' ;

DROP FUNCTION IF EXISTS roadCoords(cordPoint geometry);
CREATE OR REPLACE FUNCTION roadCoords(cordPoint geometry) RETURNS real[] AS
$BODY$
BEGIN
  RETURN roadCoords(Cast(ST_X(ST_Centroid(cordPoint)) AS real), Cast(ST_Y(ST_Centroid(cordPoint)) AS real));
END
$BODY$
LANGUAGE 'plpgsql' ;

DROP FUNCTION IF EXISTS roadCoords(cordPoint geometry, _time timestamptz);
CREATE OR REPLACE FUNCTION roadCoords(cordPoint geometry, _time timestamptz) RETURNS real[] AS
$BODY$
BEGIN
  RETURN roadCoords(cordPoint);
END
$BODY$
LANGUAGE 'plpgsql' ;

DROP FUNCTION IF EXISTS roadCoords(trajectory tgeompoint, _time timestamptz);
CREATE OR REPLACE FUNCTION roadCoords(trajectory tgeompoint, _time timestamptz) RETURNS real[] AS
$BODY$
BEGIN
  RETURN roadCoords(valueAtTimestamp(trajectory, _time));
END
$BODY$
LANGUAGE 'plpgsql' ;