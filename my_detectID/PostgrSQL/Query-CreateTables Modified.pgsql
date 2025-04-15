-- PERSON
CREATE TABLE cdmDatabaseSchema.PERSON (
	person_id integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
	gender_concept_id integer NOT NULL,
	person_source_value varchar(50),
	birthday date NOT NULL,
	first_name varchar(100) NOT NULL,
	last_name varchar(100) NOT NULL
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
