DROP FUNCTION IF EXISTS leftTurn(tfloat, int, text);
CREATE OR REPLACE FUNCTION leftTurn(itemHeadings tfloat, frameNum int, cameraId text) RETURNS boolean AS
$BODY$
DECLARE i int;
DECLARE maxAngle real;
DECLARE currentAngle real;
DECLARE LEFT_THRESHOLD real = 75;
BEGIN
    -- Turn Duration = 3sec. FPS = 30FPS. Frame 90 Frames
    i := frameNum - 90;
    maxAngle := valueAtTimestamp(itemHeadings, getTimestamp(frameNum, cameraId));

    WHILE i < frameNum + 90
    LOOP
        i := i + 1;
        currentAngle := valueAtTimestamp(itemHeadings, getTimestamp(frameNum, cameraId));
        if angleBetween(facingRelative(currentAngle, maxAngle), 0, LEFT_THRESHOLD) THEN
            RETURN true;
        END IF;
    END LOOP;

    RETURN false;
END
$BODY$
LANGUAGE 'plpgsql' ;

DROP FUNCTION IF EXISTS getTimestamp(int, text);
CREATE OR REPLACE FUNCTION getTimestamp(frameNum int, cameraId text) RETURNS timestamptz AS
$BODY$
BEGIN
    return (SELECT timestamp FROM Cameras AS c 
           WHERE c.cameraId = cameraId AND c.frameNum = frameNum);  
END
$BODY$
LANGUAGE 'plpgsql' ;