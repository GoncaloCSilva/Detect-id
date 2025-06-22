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
