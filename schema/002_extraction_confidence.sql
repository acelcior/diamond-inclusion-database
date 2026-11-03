-- 002_extraction_confidence.sql: how sure we are that a record matches what the source printed.
-- This is extraction quality, not scientific certainty: ambiguities in the source itself stay as flags.
-- Levels are computed by versioned rules (docs/confidence.md), never typed in by hand.

CREATE TABLE extraction_confidence (
    id                       INTEGER PRIMARY KEY,
    inclusion_observation_id INTEGER UNIQUE REFERENCES inclusion_observation(id),
    derived_parameter_id     INTEGER UNIQUE REFERENCES derived_parameter(id),
    diamond_observation_id   INTEGER UNIQUE REFERENCES diamond_observation(id),
    level                    TEXT NOT NULL CHECK (level IN ('high', 'medium', 'low')),
    reasons                  TEXT NOT NULL,   -- why, in plain words; one clause per rule applied
    rule_version             TEXT NOT NULL,   -- e.g. 'conf-v1'
    CHECK ((CASE WHEN inclusion_observation_id IS NULL THEN 0 ELSE 1 END)
         + (CASE WHEN derived_parameter_id     IS NULL THEN 0 ELSE 1 END)
         + (CASE WHEN diamond_observation_id   IS NULL THEN 0 ELSE 1 END) = 1)
);
