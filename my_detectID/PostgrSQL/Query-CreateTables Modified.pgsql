-- Tabelas não usadas apagadas
-- HINT DISTRIBUTE ON KEY (person_id)
CREATE TABLE cdmDatabaseSchema.PERSON (
	person_id integer PRIMARY KEY,	-- Id Utente
	gender_concept_id integer NOT NULL, -- Genero
	person_source_value varchar(50) NULL, -- Numero de Utente
	birthday date NOT NULL, -- Dia Nascimento
	first_name varchar(100) NOT NULL, -- Primeiro Nome
	last_name varchar(100) NOT NULL   -- Último Nome
);

-- HINT DISTRIBUTE ON KEY (person_id)
CREATE TABLE cdmDatabaseSchema.CONDITION_OCCURRENCE (	
	condition_occurrence_id integer PRIMARY KEY,	-- Id
	person_id integer NOT NULL,				-- Utente
	condition_start_date date NOT NULL, -- Data Diagnóstico 
	condition_source_value varchar(50) NOT NULL -- Diagnóstico Principal
);

-- HINT DISTRIBUTE ON KEY (person_id)
CREATE TABLE cdmDatabaseSchema.NOTE (	-- Queixas de Entrada, Alergias
	note_id integer PRIMARY KEY,		-- Id
	person_id integer NOT NULL,		-- Utente
	note_text TEXT NOT NULL,		-- Texto da nota
	note_type_concept_id integer NOT NULL -- Tipo de Nota
);

-- HINT DISTRIBUTE ON KEY (person_id)
CREATE TABLE cdmDatabaseSchema.OBSERVATION ( -- Evento
	observation_id integer PRIMARY KEY,		-- Id
	person_id integer NOT NULL,				-- Utente
	observation_concept_id integer NOT NULL, -- Tipo de Observação
	value_as_number NUMERIC NULL, -- Valor da Observação -> 0 Nao ativo, 1 Ativo
	observation_datetime timestamp NOT NULL -- Data de Observação
);

-- HINT DISTRIBUTE ON KEY (person_id)
CREATE TABLE cdmDatabaseSchema.VISIT_OCCURRENCE ( -- Hora e Data de Internamento
	visit_occurrence_id integer PRIMARY KEY,	-- Id
	person_id integer NOT NULL,			-- Utente
	care_site_id integer NULL, 			-- Serviço
	visit_start_datetime timestamp NOT NULL, -- Hora e Data de Internamento
	visit_end_datetime timestamp NULL -- Hora e Data de Alta
);

-- HINT DISTRIBUTE ON KEY (person_id)
CREATE TABLE cdmDatabaseSchema.MEASUREMENT ( -- Medição dos Parâmetros
	measurement_id integer PRIMARY KEY,	-- Id
	person_id integer NOT NULL,			-- Utente
	measurement_concept_id integer NOT NULL, -- Tipo de Medição
	value_as_number NUMERIC NOT NULL,		-- Valor
	measurement_datetime timestamp NOT NULL -- Data e hora da medição
);
