-- 003: compilation import (D-013). The DOI the compiler cites for a row, and indexes for ~10^4-row sources.
-- Portable SQL (SQLite and PostgreSQL).

ALTER TABLE evidence ADD COLUMN cited_doi TEXT;   -- compilations: DOI as printed by the compiler (lower-cased)

CREATE INDEX idx_assertion_inclusion   ON assertion (inclusion_observation_id);
CREATE INDEX idx_assertion_diamond     ON assertion (diamond_observation_id);
CREATE INDEX idx_assertion_set         ON assertion (inclusion_set_id);
CREATE INDEX idx_measurement_inclusion ON measurement (inclusion_observation_id);
CREATE INDEX idx_measurement_diamond   ON measurement (diamond_observation_id);
CREATE INDEX idx_value_measurement     ON measured_value (measurement_id);
CREATE INDEX idx_inclusion_diamond     ON inclusion_observation (diamond_observation_id);
CREATE INDEX idx_inclusion_publication ON inclusion_observation (publication_id);
CREATE INDEX idx_diamond_publication   ON diamond_observation (publication_id);
CREATE INDEX idx_specimen_diamond      ON specimen_identifier (diamond_observation_id);
CREATE INDEX idx_evidence_publication  ON evidence (publication_id);
