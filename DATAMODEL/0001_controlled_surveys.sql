/***
Set up table
***/

-- DROP TABLE IF EXISTS demand."TimePeriodsControlledDuringSurveyHours" CASCADE;

CREATE TABLE demand."TimePeriodsControlledDuringSurveyHours"
(
    gid INT GENERATED ALWAYS AS IDENTITY,
    "SurveyID" integer NOT NULL,
    "TimePeriodID" integer NOT NULL,
    "Controlled" boolean,

    PRIMARY KEY (gid),

    UNIQUE ("SurveyID", "TimePeriodID")
)

TABLESPACE pg_default;

ALTER TABLE demand."TimePeriodsControlledDuringSurveyHours"
    OWNER to postgres;

INSERT INTO demand."TimePeriodsControlledDuringSurveyHours" ("SurveyID", "TimePeriodID")
SELECT "SurveyID", "TimePeriodID"
FROM demand."Surveys",
(SELECT DISTINCT "NoWaitingTimeID" AS "TimePeriodID"
 FROM mhtc_operations."Supply"
 WHERE "RestrictionTypeID" IN (201, 221, 224, 217, 222, 226, 203, 207, 208) -- SYL, SRLs, ZigZags
 AND "NoWaitingTimeID" IS NOT NULL
) as w
WHERE "SurveyID" > 0;

-- Add any extras
INSERT INTO demand."TimePeriodsControlledDuringSurveyHours" ("SurveyID", "TimePeriodID")
SELECT "SurveyID", "TimePeriodID"
FROM demand."Surveys" s,
(SELECT DISTINCT "TimePeriodID"
 FROM mhtc_operations."Supply"
 WHERE "RestrictionTypeID" < 200
 AND "TimePeriodID" IS NOT NULL
 UNION
SELECT DISTINCT "NoWaitingTimeID" AS "TimePeriodID"
 FROM mhtc_operations."Supply"
 WHERE "RestrictionTypeID" > 200
 AND "NoWaitingTimeID" IS NOT NULL) AS t
WHERE "TimePeriodID" NOT IN
    (SELECT DISTINCT "TimePeriodID"
    FROM demand."TimePeriodsControlledDuringSurveyHours")
AND s."SurveyID" > 0;

-- Deal with any "At Any Time"
UPDATE demand."TimePeriodsControlledDuringSurveyHours"
SET "Controlled" = TRUE
WHERE "TimePeriodID" = 1;

UPDATE demand."TimePeriodsControlledDuringSurveyHours"
SET "Controlled" = FALSE
WHERE "TimePeriodID" = 0;

-- TODO: any others?

/***
-- With different days ...

UPDATE demand."TimePeriodsControlledDuringSurveyHours" AS t1
SET "Controlled" = COALESCE(t2."Controlled", false)
FROM demand."TimePeriodsControlledDuringSurveyHours" t2
WHERE t1."TimePeriodID" = t2."TimePeriodID"
AND t2."SurveyID" = 101
AND t1."SurveyID" IN (201, 301, 401)

***/


/***
 Tidy if time periods are removed
 
 ***/

/***

DELETE FROM demand."TimePeriodsControlledDuringSurveyHours"
WHERE "TimePeriodID" NOT IN (
SELECT DISTINCT "TimePeriodID"
 FROM mhtc_operations."Supply"
 WHERE "RestrictionTypeID" < 200
 AND "TimePeriodID" IS NOT NULL
 UNION
SELECT DISTINCT "NoWaitingTimeID" AS "TimePeriodID"
 FROM mhtc_operations."Supply"
 WHERE "RestrictionTypeID" > 200
 AND "NoWaitingTimeID" IS NOT NULL)
 
 ***/

/***
-- ALTER if imported

ALTER TABLE IF EXISTS demand."TimePeriodsControlledDuringSurveyHours"
    ADD PRIMARY KEY ("gid");
	
ALTER TABLE IF EXISTS demand."TimePeriodsControlledDuringSurveyHours"
    ADD UNIQUE ("SurveyID", "TimePeriodID");
	
***/