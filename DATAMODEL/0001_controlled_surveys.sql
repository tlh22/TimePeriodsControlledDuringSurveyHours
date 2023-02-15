/***
Set up table
***/

DROP TABLE IF EXISTS demand."TimePeriodsControlledDuringSurveyHours" CASCADE;

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
 WHERE "RestrictionTypeID" IN (201, 221, 224, 217, 222, 226) -- SYL, SRLs
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

-- TODO: any others?