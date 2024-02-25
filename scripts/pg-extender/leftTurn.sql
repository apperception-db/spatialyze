-- DROP FUNCTION IF EXISTS leftTurn(tfloat, int, text);
-- CREATE OR REPLACE FUNCTION leftTurn(itemHeadings tfloat, frameNum int, cameraId text) RETURNS boolean AS
-- $BODY$
-- DECLARE i int;
-- DECLARE maxAngle real;
-- DECLARE currentAngle real;
-- BEGIN
--     -- Turn Duration = 3sec. FPS = 30FPS. Frame 90 Frames
--     i := frameNum - 90;
--     maxAngle := valueAtTimestamp(itemHeadings, getTimestamp(frameNum, cameraId));

--     WHILE i < frameNum + 90
--     LOOP
--         i := i + 30;
--         currentAngle := valueAtTimestamp(itemHeadings, getTimestamp(frameNum, cameraId));
--         if angleBetween(facingRelative(maxAngle, currentAngle), 75, 100) THEN
--             RETURN true;
--         END IF;
--         maxAngle := MAX(maxAngle, currentAngle);
--     END LOOP;

--     RETURN false;
-- END
-- $BODY$
-- LANGUAGE 'plpgsql' ;

-- DROP FUNCTION IF EXISTS leftTurn(tfloat, int, text);
-- CREATE OR REPLACE FUNCTION leftTurn(itemHeadings tfloat, frameNum int, cameraId text) RETURNS boolean AS
-- $BODY$
-- DECLARE nextFrame int;
-- DECLARE prevFrame int;
-- DECLARE currentAngle real;
-- DECLARE nextAngle real;
-- DECLARE prevAngle real;
-- BEGIN
--     -- Turn Duration = 2sec. FPS = 30FPS. Frame 60 Frames
--     nextFrame := frameNum + 60;
--     prevFrame := frameNum - 60;
    
--     currentAngle := valueAtTimestamp(itemHeadings, getTimestamp(frameNum, cameraId));
--     nextAngle = valueAtTimestamp(itemHeadings, getTimestamp(nextFrame, cameraId));
--     prevAngle = valueAtTimestamp(itemHeadings, getTimestamp(prevFrame, cameraId));

--     if angleBetween(facingRelative(nextAngle, currentAngle), 50, 145) THEN
--         RETURN true;
--     END IF;
--     if angleBetween(facingRelative(currentAngle, prevAngle), 50, 145) THEN
--         RETURN true;
--     END IF;
--     if angleBetween(facingRelative(nextAngle, prevAngle), 50, 145) THEN
--         RETURN true;
--     END IF;
    
--     RETURN false;
-- END
-- $BODY$
-- LANGUAGE 'plpgsql' ;

-- DROP FUNCTION IF EXISTS getTimestamp(int, text);
-- CREATE OR REPLACE FUNCTION getTimestamp(frame int, camId text) RETURNS timestamptz AS
-- $BODY$
-- BEGIN
--     return (SELECT timestamp FROM Camera AS c 
--            WHERE c.cameraId = camId AND c.frameNum = frame);  
-- END
-- $BODY$
-- LANGUAGE 'plpgsql' ;




-- DROP FUNCTION IF EXISTS leftTurn(tgeompoint, tfloat, int, text);
-- CREATE OR REPLACE FUNCTION leftTurn(translations tgeompoint, itemHeadings tfloat, frameNum int, cameraId text) RETURNS boolean AS
-- $BODY$
-- DECLARE nextFrame int;
-- DECLARE prevFrame int;
-- DECLARE currentAngle real;
-- DECLARE nextAngle real;
-- DECLARE prevAngle real;
-- DECLARE currentPoint geometry;
-- DECLARE nextPoint geometry;
-- DECLARE prevPoint geometry;
-- BEGIN
--     -- Turn Duration = 2sec. FPS = 30FPS. Frame 60 Frames
--     nextFrame := frameNum + 1;
--     prevFrame := frameNum - 1;
    
--     currentAngle := valueAtTimestamp(itemHeadings, getTimestamp(frameNum, cameraId));
--     nextAngle = valueAtTimestamp(itemHeadings, getTimestamp(nextFrame, cameraId));
--     prevAngle = valueAtTimestamp(itemHeadings, getTimestamp(prevFrame, cameraId));

--     currentPoint := valueAtTimestamp(translations, getTimestamp(frameNum, cameraId));
--     nextPoint = valueAtTimestamp(translations, getTimestamp(nextFrame, cameraId));
--     prevPoint = valueAtTimestamp(translations, getTimestamp(prevFrame, cameraId));

--     if ST_X(ConvertCamera(nextPoint, currentPoint, currentAngle)) < -1 THEN
--         RETURN true;
--     END IF;
--     if ST_X(ConvertCamera(currentPoint, prevPoint, prevAngle)) < -1 THEN
--         RETURN true;
--     END IF;
--     if ST_X(ConvertCamera(nextPoint, prevPoint, prevAngle)) < -1 THEN
--         RETURN true;
--     END IF;
    
--     RETURN false;
-- END
-- $BODY$
-- LANGUAGE 'plpgsql' ;


DROP FUNCTION IF EXISTS leftTurn(geometry, float, int, text, text);
CREATE OR REPLACE FUNCTION leftTurn(translation geometry, itemHeading float, frameNum int, obj_Id text, cameraId text) RETURNS boolean AS
$BODY$
DECLARE nextFrame int;
DECLARE prevFrame int;
DECLARE currentAngle real;
DECLARE nextAngle real;
DECLARE prevAngle real;
DECLARE currentPoint geometry;
DECLARE nextPoint geometry;
DECLARE prevPoint geometry;
BEGIN
    -- Turn Duration = 2sec. FPS = 30FPS. Frame 60 Frames
    nextFrame := frameNum + 1;
    prevFrame := frameNum - 1;
    
    currentAngle := itemHeading::real;
    nextAngle = (SELECT itemHeading from Item_Trajectory2 AS t WHERE obj_Id = t.itemId AND t.frameNum = nextFrame);
    prevAngle = (SELECT itemHeading from Item_Trajectory2 AS t WHERE obj_Id = t.itemId AND t.frameNum = prevFrame);

    currentPoint := translation;
    nextPoint = (SELECT translation from Item_Trajectory2 AS t WHERE obj_Id = t.itemId AND t.frameNum = nextFrame);
    prevPoint = (SELECT translation from Item_Trajectory2 AS t WHERE obj_Id = t.itemId AND t.frameNum = prevFrame);

    if ST_X(ConvertCamera(nextPoint, currentPoint, currentAngle)) < -1 THEN
        RETURN true;
    END IF;
    if ST_X(ConvertCamera(currentPoint, prevPoint, prevAngle)) < -1 THEN
        RETURN true;
    END IF;
    if ST_X(ConvertCamera(nextPoint, prevPoint, prevAngle)) < -1 THEN
        RETURN true;
    END IF;
    
    RETURN false;
END
$BODY$
LANGUAGE 'plpgsql' ;