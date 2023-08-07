CREATE OR REPLACE FUNCTION greaterThan(a geometry, b geometry) RETURNS boolean AS
$BODY$
BEGIN
    RETURN ST_X(a) > ST_X(b) AND ST_Y(a) > ST_Y(b);
END
$BODY$
LANGUAGE 'plpgsql' ;

CREATE OR REPLACE FUNCTION greaterThan(a geometry, b real[]) RETURNS boolean AS
$BODY$
BEGIN
  RETURN greaterThan(a, ST_MakePoint(b[1], b[2]));
END
$BODY$
LANGUAGE 'plpgsql' ;

DROP OPERATOR IF EXISTS > (geometry, real[]);
CREATE OPERATOR  > (
  LEFTARG = geometry,
  RIGHTARG = real[],
  PROCEDURE = greaterThan,
  COMMUTATOR = <,
  NEGATOR = <=
);

CREATE OR REPLACE FUNCTION lessThan(a geometry, b geometry) RETURNS boolean AS
$BODY$
BEGIN
    RETURN ST_X(a) < ST_X(b) AND ST_Y(a) < ST_Y(b);
END
$BODY$
LANGUAGE 'plpgsql' ;

CREATE OR REPLACE FUNCTION lessThan(a geometry, b real[]) RETURNS boolean AS
$BODY$
BEGIN
  RETURN lessThan(a, ST_MakePoint(b[1], b[2]));
END
$BODY$
LANGUAGE 'plpgsql' ;

DROP OPERATOR IF EXISTS < (geometry, real[]);
CREATE OPERATOR < (
  LEFTARG = geometry,
  RIGHTARG = real[],
  PROCEDURE = lessThan,
  COMMUTATOR = >,
  NEGATOR = >=
);

CREATE OR REPLACE FUNCTION greaterOrEqual(a geometry, b geometry) RETURNS boolean AS
$BODY$
BEGIN
    RETURN ST_X(a) >= ST_X(b) AND ST_Y(a) >= ST_Y(b);
END
$BODY$
LANGUAGE 'plpgsql' ;

CREATE OR REPLACE FUNCTION greaterOrEqual(a geometry, b real[]) RETURNS boolean AS
$BODY$
BEGIN
  RETURN greaterOrEqual(a, ST_MakePoint(b[1], b[2]));
END
$BODY$
LANGUAGE 'plpgsql' ;

DROP OPERATOR IF EXISTS >= (geometry, real[]);
CREATE OPERATOR >= (
  LEFTARG = geometry,
  RIGHTARG = real[],
  PROCEDURE = greaterOrEqual,
  COMMUTATOR = <=,
  NEGATOR = <
);

CREATE OR REPLACE FUNCTION lessOrEqual(a geometry, b geometry) RETURNS boolean AS
$BODY$
BEGIN
    RETURN ST_X(a) <= ST_X(b) AND ST_Y(a) <= ST_Y(b);
END
$BODY$
LANGUAGE 'plpgsql' ;

CREATE OR REPLACE FUNCTION lessOrEqual(a geometry, b real[]) RETURNS boolean AS
$BODY$
BEGIN
  RETURN lessOrEqual(a, ST_MakePoint(b[1], b[2]));
END
$BODY$
LANGUAGE 'plpgsql' ;

DROP OPERATOR IF EXISTS <= (geometry, real[]);
CREATE OPERATOR <= (
  LEFTARG = geometry,
  RIGHTARG = real[],
  PROCEDURE = lessOrEqual,
  COMMUTATOR = >=,
  NEGATOR = >
);

CREATE OR REPLACE FUNCTION Equal(a geometry, b geometry) RETURNS boolean AS
$BODY$
BEGIN
    RETURN ST_X(a) == ST_X(b) AND ST_Y(a) == ST_Y(b);
END
$BODY$
LANGUAGE 'plpgsql' ;

CREATE OR REPLACE FUNCTION Equal(a geometry, b real[]) RETURNS boolean AS
$BODY$
BEGIN
  RETURN Equal(a, ST_MakePoint(b[1], b[2]));
END
$BODY$
LANGUAGE 'plpgsql' ;

DROP OPERATOR IF EXISTS == (geometry, real[]);
CREATE OPERATOR == (
  LEFTARG = geometry,
  RIGHTARG = real[],
  PROCEDURE = Equal,
  COMMUTATOR = ==,
  NEGATOR = !=
);
