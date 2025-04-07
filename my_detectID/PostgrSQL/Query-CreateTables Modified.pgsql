-- Tabelas nao usadas apagadas
--HINT DISTRIBUTE ON KEY (person_id)
CREATE TABLE cdmDatabaseSchema.PERSON (
			person_id integer NOT NULL,
			gender_concept_id integer NOT NULL,
			year_of_birth integer NOT NULL,
			month_of_birth integer NULL,
			day_of_birth integer NULL,
			birth_datetime TIMESTAMP NULL,
			race_concept_id integer  NULL,
			ethnicity_concept_id integer  NULL,
			location_id integer NULL,
			provider_id integer NULL,
			care_site_id integer NULL,
			person_source_value varchar(50) NULL,
			gender_source_value varchar(50) NULL,
			gender_source_concept_id integer NULL,
			race_source_value varchar(50) NULL,
			race_source_concept_id integer NULL,
			ethnicity_source_value varchar(50) NULL,
			ethnicity_source_concept_id integer NULL );

--HINT DISTRIBUTE ON KEY (person_id)
CREATE TABLE cdmDatabaseSchema.CONDITION_OCCURRENCE (
			condition_occurrence_id integer NOT NULL,
			person_id integer NOT NULL,
			condition_concept_id integer NOT NULL,
			condition_start_date date NOT NULL,
			condition_start_datetime TIMESTAMP NULL,
			condition_end_date date NULL,
			condition_end_datetime TIMESTAMP NULL,
			condition_type_concept_id integer NOT NULL,
			condition_status_concept_id integer NULL,
			stop_reason varchar(20) NULL,
			provider_id integer NULL,
			visit_occurrence_id integer NULL,
			visit_detail_id integer NULL,
			condition_source_value varchar(50) NULL,
			condition_source_concept_id integer NULL,
			condition_status_source_value varchar(50) NULL );
			
--HINT DISTRIBUTE ON KEY (person_id)
CREATE TABLE cdmDatabaseSchema.NOTE (
			note_id integer NOT NULL,
			person_id integer NOT NULL,
			note_date date NOT NULL,
			note_datetime TIMESTAMP NULL,
			note_type_concept_id integer NOT NULL,
			note_class_concept_id integer NOT NULL,
			note_title varchar(250) NULL,
			note_text TEXT NOT NULL,
			encoding_concept_id integer NOT NULL,
			language_concept_id integer NOT NULL,
			provider_id integer NULL,
			visit_occurrence_id integer NULL,
			visit_detail_id integer NULL,
			note_source_value varchar(50) NULL,
			note_event_id bigint NULL,
			note_event_field_concept_id integer NULL );

--HINT DISTRIBUTE ON KEY (person_id)
CREATE TABLE cdmDatabaseSchema.OBSERVATION (
			observation_id integer NOT NULL,
			person_id integer NOT NULL,
			observation_concept_id integer NOT NULL,
			observation_date date NOT NULL,
			observation_datetime TIMESTAMP NULL,
			observation_type_concept_id integer NOT NULL,
			value_as_number NUMERIC NULL,
			value_as_string varchar(60) NULL,
			value_as_concept_id Integer NULL,
			qualifier_concept_id integer NULL,
			unit_concept_id integer NULL,
			provider_id integer NULL,
			visit_occurrence_id integer NULL,
			visit_detail_id integer NULL,
			observation_source_value varchar(50) NULL,
			observation_source_concept_id integer NULL,
			unit_source_value varchar(50) NULL,
			qualifier_source_value varchar(50) NULL,
			value_source_value varchar(50) NULL,
			observation_event_id bigint NULL,
			obs_event_field_concept_id integer NULL );

--HINT DISTRIBUTE ON KEY (person_id)
CREATE TABLE cdmDatabaseSchema.VISIT_OCCURRENCE (
			visit_occurrence_id integer NOT NULL,
			person_id integer NOT NULL,
			visit_concept_id integer NOT NULL,
			visit_start_date date NOT NULL,
			visit_start_datetime TIMESTAMP NULL,
			visit_end_date date NOT NULL,
			visit_end_datetime TIMESTAMP NULL,
			visit_type_concept_id Integer NOT NULL,
			provider_id integer NULL,
			care_site_id integer NULL,
			visit_source_value varchar(50) NULL,
			visit_source_concept_id integer NULL,
			admitted_from_concept_id integer NULL,
			admitted_from_source_value varchar(50) NULL,
			discharged_to_concept_id integer NULL,
			discharged_to_source_value varchar(50) NULL,
			preceding_visit_occurrence_id integer NULL );

--HINT DISTRIBUTE ON RANDOM
CREATE TABLE cdmDatabaseSchema.CARE_SITE (
			care_site_id integer NOT NULL,
			care_site_name varchar(255) NULL,
			place_of_service_concept_id integer NULL,
			location_id integer NULL,
			care_site_source_value varchar(50) NULL,
			place_of_service_source_value varchar(50) NULL );

--HINT DISTRIBUTE ON KEY (person_id)
CREATE TABLE cdmDatabaseSchema.MEASUREMENT (
			measurement_id integer NOT NULL,
			person_id integer NOT NULL,
			measurement_concept_id integer NOT NULL,
			measurement_date date NOT NULL,
			measurement_datetime TIMESTAMP NULL,
			measurement_time varchar(10) NULL,
			measurement_type_concept_id integer NOT NULL,
			operator_concept_id integer NULL,
			value_as_number NUMERIC NULL,
			value_as_concept_id integer NULL,
			unit_concept_id integer NULL,
			range_low NUMERIC NULL,
			range_high NUMERIC NULL,
			provider_id integer NULL,
			visit_occurrence_id integer NULL,
			visit_detail_id integer NULL,
			measurement_source_value varchar(50) NULL,
			measurement_source_concept_id integer NULL,
			unit_source_value varchar(50) NULL,
			unit_source_concept_id integer NULL,
			value_source_value varchar(50) NULL,
			measurement_event_id bigint NULL,
			meas_event_field_concept_id integer NULL );
