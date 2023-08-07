/* Used when a stepwise interplotation is used to define headings */
DROP FUNCTION IF EXISTS headingAtTimestamp(tfloat, timestamptz); 
CREATE OR REPLACE FUNCTION headingAtTimestamp(headings tfloat, t timestamptz) RETURNS float AS
$BODY$
declare i integer := 2;
BEGIN
    IF (t <= startTimestamp(headings)) THEN
        RETURN valueAtTimestamp(headings, startTimestamp(headings));
    END IF;
    IF (t >= endTimestamp(headings)) THEN
        RETURN valueAtTimestamp(headings, endTimestamp(headings));
    END IF;

    RETURN valueAtTimestamp(headings, t);
END
$BODY$
LANGUAGE 'plpgsql' ;

/* Used when a linear interplotation is used to define headings */
DROP FUNCTION IF EXISTS headingAtTimestampLinear(tfloat, timestamptz); 
CREATE OR REPLACE FUNCTION headingAtTimestampLinear(headings tfloat, t timestamptz) RETURNS float AS
$BODY$
declare i integer := 2;
BEGIN
    IF (t <= startTimestamp(headings)) THEN
        RETURN valueAtTimestamp(headings, startTimestamp(headings));
    END IF;
    IF (t >= endTimestamp(headings)) THEN
        RETURN valueAtTimestamp(headings, endTimestamp(headings));
    END IF;

    WHILE i <= numTimestamps(headings) LOOP
        IF (t < timestampN(headings, i)) THEN
            RETURN valueAtTimestamp(headings, timestampN(headings, i - 1));
        END IF;
        i := i + 1;
    END LOOP;
END
$BODY$
LANGUAGE 'plpgsql' ;