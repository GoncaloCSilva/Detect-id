-- Inserir dados na tabela PERSON
INSERT INTO cdmdatabaseschema.PERSON (
    person_id, gender_concept_id, year_of_birth, month_of_birth, day_of_birth, person_source_value
)
VALUES
    (1, 8507, 2002, 10, 25, 'UT001'),  -- Gonçalo Silva
    (2, 8532, 2005, 6, 18, 'UT002'),   -- Violeta Santos
    (3, 8507, 2002, 5, 24, 'UT003'),   -- Diogo Lobo
    (4, 8532, 1971, 6, 7, 'UT004'),    -- Claudia Silva
    (5, 8507, 1970, 5, 11, 'UT005');   -- Diogo Silva

-- Inserir dados na tabela PERSON_DETAILS
INSERT INTO cdmdatabaseschema.PERSON_DETAILS (
    person_id, first_name, last_name
)
VALUES
    (1, 'Gonçalo', 'Silva'),
    (2, 'Violeta', 'Santos'),
    (3, 'Diogo', 'Lobo'),
    (4, 'Claudia', 'Silva'),
    (5, 'Diogo', 'Silva');
