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
DROP TABLE IF EXISTS cdmdatabaseschema.MEASUREMENT_EXT CASCADE;

-- PERSON
-- This table stores information about a person, such as their gender, birthday.
CREATE TABLE cdmDatabaseSchema.PERSON (
	person_id integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
	gender_concept_id integer NOT NULL,
	person_source_value varchar(50),
	birthday date NOT NULL 
);

-- PERSON_EXT
-- This table extends the PERSON table to include additional information such as first name, last name and the probability calculated by the models of 
-- the general-to-event.
CREATE TABLE cdmDatabaseSchema.PERSON_EXT (
    person_ptr_id  integer PRIMARY KEY,
    first_name varchar(100) NOT NULL,
    last_name varchar(100) NOT NULL,
	probability_km float,
	probability_rsf float,
    FOREIGN KEY (person_ptr_id) REFERENCES cdmDatabaseSchema.PERSON (person_id)
);

-- CONDITION_OCCURRENCE
-- This table stores information about medical conditions that a person is experiencing.
CREATE TABLE cdmDatabaseSchema.CONDITION_OCCURRENCE (
	condition_occurrence_id integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
	person_id integer NOT NULL,
	condition_start_date date NOT NULL,
	condition_source_value varchar(50) NOT NULL
);

-- NOTE
-- This table stores notes related to a person, such as allergies.
CREATE TABLE cdmDatabaseSchema.NOTE (
	note_id integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
	person_id integer NOT NULL,
	note_text TEXT NOT NULL,
	note_type_concept_id integer NOT NULL
);

-- OBSERVATION
-- This table stores information about the events that happened to a person.
CREATE TABLE cdmDatabaseSchema.OBSERVATION (
	observation_id integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
	person_id integer NOT NULL,
	observation_concept_id integer NOT NULL,
	value_as_number float,
	observation_datetime timestamp NOT NULL
);

-- CARE_SITE
-- This table stores information about care sites where medical services are provided.
CREATE TABLE cdmDatabaseSchema.CARE_SITE(
	care_site_id integer PRIMARY KEY,
	care_site_name varchar(100) NOT NULL
);


-- VISIT_OCCURRENCE
-- This table stores information about time periods when a person was under medical care.
-- It includes details such as the start and end times of the visit, the person involved, and the care site.
CREATE TABLE cdmDatabaseSchema.VISIT_OCCURRENCE (
	visit_occurrence_id integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
	person_id integer NOT NULL,
	care_site_id integer,
	visit_start_datetime timestamp NOT NULL,
	visit_end_datetime timestamp,
	FOREIGN KEY (care_site_id) REFERENCES cdmDatabaseSchema.care_site (care_site_id)
);

-- MEASUREMENT
-- This table stores information about the measurments taken for a person.
-- It includes details such as the person involved, which parameter was measured and the value of the measurement
CREATE TABLE cdmDatabaseSchema.MEASUREMENT (
	measurement_id integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
	person_id integer NOT NULL,
	measurement_concept_id integer NOT NULL,
	value_as_number float NOT NULL,
	measurement_datetime timestamp NOT NULL,
	range_low float NOT NULL,
	range_high float NOT NULL
);

-- MEASUREMENT
-- This table extends the MEASUREMENT table to include additional information such as the probability calculated by the models for the given measurement.
CREATE TABLE cdmDatabaseSchema.MEASUREMENT_EXT (
    measurement_ptr_id  integer PRIMARY KEY,
	probability_km float,
	probability_rsf float,
	FOREIGN KEY (measurement_ptr_id) REFERENCES cdmDatabaseSchema.MEASUREMENT (measurement_id)
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

