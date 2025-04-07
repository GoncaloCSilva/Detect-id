-- FOREIGN KEYS

-- CONDITION_OCCURRENCE → PERSON
ALTER TABLE cdmDatabaseSchema.CONDITION_OCCURRENCE
ADD CONSTRAINT fk_condition_person
FOREIGN KEY (person_id)
REFERENCES cdmDatabaseSchema.PERSON(person_id);

-- NOTE → PERSON
ALTER TABLE cdmDatabaseSchema.NOTE
ADD CONSTRAINT fk_note_person
FOREIGN KEY (person_id)
REFERENCES cdmDatabaseSchema.PERSON(person_id);

-- OBSERVATION → PERSON
ALTER TABLE cdmDatabaseSchema.OBSERVATION
ADD CONSTRAINT fk_observation_person
FOREIGN KEY (person_id)
REFERENCES cdmDatabaseSchema.PERSON(person_id);

-- VISIT_OCCURRENCE → PERSON
ALTER TABLE cdmDatabaseSchema.VISIT_OCCURRENCE
ADD CONSTRAINT fk_visit_person
FOREIGN KEY (person_id)
REFERENCES cdmDatabaseSchema.PERSON(person_id);

-- MEASUREMENT → PERSON
ALTER TABLE cdmDatabaseSchema.MEASUREMENT
ADD CONSTRAINT fk_measurement_person
FOREIGN KEY (person_id)
REFERENCES cdmDatabaseSchema.PERSON(person_id);

-- PERSON_DETAILS → PERSON
ALTER TABLE cdmDatabaseSchema.PERSON_DETAILS
ADD CONSTRAINT fk_persondetails_person
FOREIGN KEY (person_id)
REFERENCES cdmDatabaseSchema.PERSON(person_id);
