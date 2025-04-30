DROP TABLE IF EXISTS cdmdatabaseschema.person CASCADE;
DROP TABLE IF EXISTS cdmdatabaseschema.observation_period CASCADE;
DROP TABLE IF EXISTS cdmdatabaseschema.visit_occurrence CASCADE;
DROP TABLE IF EXISTS cdmdatabaseschema.measurement CASCADE;
DROP TABLE IF EXISTS cdmdatabaseschema.drug_exposure CASCADE;
DROP TABLE IF EXISTS cdmdatabaseschema.condition_occurrence CASCADE;
DROP TABLE IF EXISTS cdmdatabaseschema.care_site CASCADE;
DROP TABLE IF EXISTS cdmdatabaseschema.provider CASCADE;
DROP TABLE IF EXISTS cdmdatabaseschema.payer_plan_period CASCADE;
DROP TABLE IF EXISTS cdmdatabaseschema.visit_detail CASCADE;
DROP TABLE IF EXISTS cdmdatabaseschema.observation CASCADE;
DROP TABLE IF EXISTS cdmdatabaseschema.measurement_era CASCADE;
DROP TABLE IF EXISTS cdmdatabaseschema.drug_era CASCADE;
DROP TABLE IF EXISTS cdmdatabaseschema.condition_era CASCADE;
DROP TABLE IF EXISTS cdmdatabaseschema.cohort CASCADE;
DROP TABLE IF EXISTS cdmdatabaseschema.cohort_definition CASCADE;
DROP TABLE IF EXISTS cdmdatabaseschema.coexposure CASCADE;
DROP TABLE IF EXISTS cdmdatabaseschema.cost CASCADE;
DROP TABLE IF EXISTS cdmdatabaseschema.device_exposure CASCADE;
DROP TABLE IF EXISTS cdmdatabaseschema.location CASCADE;
DROP TABLE IF EXISTS cdmdatabaseschema.note CASCADE;
DROP TABLE IF EXISTS cdmdatabaseschema.note_nlp CASCADE;
DROP TABLE IF EXISTS cdmdatabaseschema.payer_plan_period CASCADE;
DROP TABLE IF EXISTS cdmdatabaseschema.relationship CASCADE;
DROP TABLE IF EXISTS cdmdatabaseschema.specimen CASCADE;
DROP TABLE IF EXISTS cdmdatabaseschema.survey_response CASCADE;
DROP TABLE IF EXISTS cdmdatabaseschema.cdm_source CASCADE;
DROP TABLE IF EXISTS cdmdatabaseschema.concept CASCADE;
DROP TABLE IF EXISTS cdmdatabaseschema.concept_ancestor CASCADE;
DROP TABLE IF EXISTS cdmdatabaseschema.concept_class CASCADE;
DROP TABLE IF EXISTS cdmdatabaseschema.concept_relationship CASCADE;
DROP TABLE IF EXISTS cdmdatabaseschema.concept_synonym CASCADE;
DROP TABLE IF EXISTS cdmdatabaseschema.death CASCADE;
DROP TABLE IF EXISTS cdmdatabaseschema.domain CASCADE;
DROP TABLE IF EXISTS cdmdatabaseschema.dose_era CASCADE;
DROP TABLE IF EXISTS cdmdatabaseschema.drug_strength CASCADE;
DROP TABLE IF EXISTS cdmdatabaseschema.episode CASCADE;
DROP TABLE IF EXISTS cdmdatabaseschema.episode_event CASCADE;
DROP TABLE IF EXISTS cdmdatabaseschema.fact_relationship CASCADE;
DROP TABLE IF EXISTS cdmdatabaseschema.metadata CASCADE;
DROP TABLE IF EXISTS cdmdatabaseschema.procedure_occurrence CASCADE;
DROP TABLE IF EXISTS cdmdatabaseschema.source_to_concept_map CASCADE;
DROP TABLE IF EXISTS cdmdatabaseschema.vocabulary CASCADE;
DROP TABLE IF EXISTS cdmdatabaseschema.person_ext CASCADE;

-- PERSON
CREATE TABLE cdmDatabaseSchema.PERSON (
	person_id integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
	gender_concept_id integer NOT NULL,
	person_source_value varchar(50),
	birthday date NOT NULL --,
	-- first_name varchar(100) NOT NULL,
	-- last_name varchar(100) NOT NULL
);

CREATE TABLE cdmDatabaseSchema.PERSON_EXT (
    person_ptr_id  integer PRIMARY KEY,
    first_name varchar(100) NOT NULL,
    last_name varchar(100) NOT NULL,
    FOREIGN KEY (person_ptr_id) REFERENCES cdmDatabaseSchema.PERSON (person_id)
);

-- CONDITION_OCCURRENCE
CREATE TABLE cdmDatabaseSchema.CONDITION_OCCURRENCE (
	condition_occurrence_id integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
	person_id integer NOT NULL,
	condition_start_date date NOT NULL,
	condition_source_value varchar(50) NOT NULL
);

-- NOTE
CREATE TABLE cdmDatabaseSchema.NOTE (
	note_id integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
	person_id integer NOT NULL,
	note_text TEXT NOT NULL,
	note_type_concept_id integer NOT NULL
);

-- OBSERVATION
CREATE TABLE cdmDatabaseSchema.OBSERVATION (
	observation_id integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
	person_id integer NOT NULL,
	observation_concept_id integer NOT NULL,
	value_as_number NUMERIC,
	observation_datetime timestamp NOT NULL
);

-- VISIT_OCCURRENCE
CREATE TABLE cdmDatabaseSchema.VISIT_OCCURRENCE (
	visit_occurrence_id integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
	person_id integer NOT NULL,
	care_site_id integer,
	visit_start_datetime timestamp NOT NULL,
	visit_end_datetime timestamp
);

-- MEASUREMENT
CREATE TABLE cdmDatabaseSchema.MEASUREMENT (
	measurement_id integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
	person_id integer NOT NULL,
	measurement_concept_id integer NOT NULL,
	value_as_number NUMERIC NOT NULL,
	measurement_datetime timestamp NOT NULL
);

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

