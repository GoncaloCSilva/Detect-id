import pandas as pd
import random
from datetime import datetime
from utentes.models import Person, Measurement, ConditionOccurrence, Note, Observation, VisitOccurrence

file_path = "detectid.csv"
df = pd.read_csv(file_path)

df.drop(columns=["Tempo", "Evento"], inplace=True)
df.rename(columns=lambda x: x.strip().replace("\n", " "), inplace=True)

numeric_cols = df.select_dtypes(include='number').columns
df[numeric_cols] = df[numeric_cols].fillna(df[numeric_cols].mean())

df["NIVEL DE CONSCIÊNCIA"] = pd.to_numeric(df["NIVEL DE CONSCIÊNCIA"], errors='coerce')
media_nivel = int(df["NIVEL DE CONSCIÊNCIA"].mean().round())
df["NIVEL DE CONSCIÊNCIA"].fillna(media_nivel, inplace=True)

df["Dia de Medição"] = df["Dia de Medição"].astype(str)
df["Hora de Medição"] = df["Hora de Medição"].astype(str)
df["datetime"] = pd.to_datetime(df["Dia de Medição"] + " " + df["Hora de Medição"], dayfirst=True, errors="coerce")
df["person_id"] = df["Pessoa"].str.extract(r"(\d+)").astype(int)
df["Data de Nascimento"] = pd.to_datetime(df["Data de Nascimento"], format='%d/%m/%Y', errors='coerce').dt.date

# Inserir dados na tabela Person
pessoas_adicionadas = set()
for _, row in df.iterrows():
    pid = row["person_id"]
    if pid not in pessoas_adicionadas:
        genero = 1 if row['Genero'] == 'Masculino' else 0
        Person.objects.create(
            person_id=pid,
            gender_concept_id=genero,
            person_source_value="12345555",
            birthday=row["Data de Nascimento"],
            first_name=row["Primeiro Nome"],
            last_name=row["Último Nome"]
        )
        pessoas_adicionadas.add(pid)

print("Pessoas inseridas!")

# Tabela MEASUREMENT
measurement_concepts = {
    "SpO2": 1,
    "NECESSIDADE DE O2": 2,
    "FREQUÊNCIA CARDIACA": 3,
    "TA Sistólica": 4,
    "TA Diastólica": 5,
    "TEMPERATURA": 6,
    "NIVEL DE CONSCIÊNCIA": 7,
    "DOR": 8,
}

measurement_id = 1
for _, row in df.iterrows():
    for field, concept_id in measurement_concepts.items():
        Measurement.objects.create(
            measurement_id=measurement_id,
            person_id=row["person_id"],
            measurement_concept_id=concept_id,
            value_as_number=row[field],
            measurement_datetime=row["datetime"]
        )
        measurement_id += 1

print("Medições inseridas!")

# Tabela CONDITION_OCCURRENCE
diagnosticos = [
    "Hipertensão arterial", "Diabetes tipo 2", "Insuficiência cardíaca", "DPOC", "Asma",
    "Enfarte agudo do miocárdio", "AVC isquémico", "Pneumonia", "Fratura do fémur", "Cancro do pulmão",
    "Insuficiência renal crónica", "Hepatite C", "Cirrose hepática", "Septicemia", "Hipotiroidismo",
    "Doença de Alzheimer", "Parkinson", "Lombalgia crónica", "Esquizofrenia", "Transtorno bipolar",
    "Depressão major", "Anemia ferropriva", "Gastrite aguda", "Úlcera péptica", "Infecção urinária",
    "COVID-19", "Apneia do sono"
]

first_dates = df.groupby("person_id")["datetime"].min().reset_index()
for i, row in first_dates.iterrows():
    ConditionOccurrence.objects.create(
        condition_occurrence_id=i + 1,
        person_id=row["person_id"],
        condition_start_date=row["datetime"].date(),
        condition_source_value=random.choice(diagnosticos)
    )

print("Diagnósticos inseridos!")

# Tabela NOTE
queixas = ["Dor abdominal", "Tosse persistente", "Febre alta", "Fadiga extrema", "Dificuldade respiratória", "Vómitos", "Tonturas", "Palpitações"]
alergias = ["Alergia a penicilina", "Intolerância à lactose", "Alergia a frutos secos", "Alergia a marisco", "Alergia ao pólen", "Alergia a anti-inflamatórios"]

note_id = 1
for person_id in df["person_id"].unique():
    Note.objects.create(
        note_id=note_id,
        person_id=person_id,
        note_text=random.choice(queixas),
        note_type_concept_id=1
    )
    note_id += 1

    if random.random() < 0.5:
        Note.objects.create(
            note_id=note_id,
            person_id=person_id,
            note_text=random.choice(alergias),
            note_type_concept_id=2
        )
        note_id += 1

print("Notas inseridas!")

# Tabela OBSERVATION
events = {
    "DESCOMPENSAÇÃO": 1,
    "Ativação Médico": 2,
    "Aumento da Vigilância": 3,
    "Via Área Ameaçada": 4
}

obs_id = 1
for _, row in df.iterrows():
    for field, concept_id in events.items():
        Observation.objects.create(
            observation_id=obs_id,
            person_id=row["person_id"],
            observation_concept_id=concept_id,
            value_as_number=row[field],
            observation_datetime=row["datetime"]
        )
        obs_id += 1

print("Observações inseridas!")

# Tabela VISIT_OCCURRENCE
visitas = df.loc[df.groupby("person_id")["datetime"].idxmin(), ["person_id", "datetime", "Serviço"]].reset_index(drop=True)
for i, row in visitas.iterrows():
    VisitOccurrence.objects.create(
        visit_occurrence_id=i + 1,
        person_id=row["person_id"],
        care_site_id=row["Serviço"],
        visit_start_datetime=row["datetime"]
    )

print("Visitas inseridas!")



# import psycopg2
# from psycopg2.extras import execute_values
# import random

# file_path = "detectid.csv"
# df = pd.read_csv(file_path)


# # Tempo tem que ser calculado logo nao entra na base de dados
# # Evento foi uma experiencia, tambem nao entra
# df_cleaned = df.drop(columns=["Tempo", "Evento"])

# df_cleaned.rename(columns=lambda x: x.strip().replace("\n", " "), inplace=True)

# # Valores Omissos preenchidos com média
# numeric_cols = df_cleaned.select_dtypes(include='number').columns
# df_cleaned[numeric_cols] = df_cleaned[numeric_cols].fillna(df_cleaned[numeric_cols].mean())

# # Converter para numérico (caso haja strings ou espaços)
# df_cleaned["NIVEL DE CONSCIÊNCIA"] = pd.to_numeric(df_cleaned["NIVEL DE CONSCIÊNCIA"], errors='coerce')

# # Calcular a média ignorando os NaNs e arredondar para inteiro
# media_nivel = int(df_cleaned["NIVEL DE CONSCIÊNCIA"].mean().round())

# # Preencher os NaNs com a média
# df_cleaned["NIVEL DE CONSCIÊNCIA"].fillna(media_nivel, inplace=True)

# # Garantir que 'Dia' e 'Hora' são string
# df_cleaned["Dia de Medição"] = df_cleaned["Dia de Medição"].astype(str)
# df_cleaned["Hora de Medição"] = df_cleaned["Hora de Medição"].astype(str)

# # Juntar as colunas 'Dia' e 'Hora' e converter para datetime com formato automático
# df_cleaned["datetime"] = pd.to_datetime(df_cleaned["Dia de Medição"] + " " + df_cleaned["Hora de Medição"], dayfirst=True, errors="coerce")

# df_cleaned["person_id"] = df_cleaned["Pessoa"].str.extract(r"(\d+)").astype(int)



# # Conectar à base de dados
# conn = psycopg2.connect(
#     dbname="detectid",
#     user="postgres",
#     password="Goncalo123",
#     host="localhost",
#     port="5432"
# )

# cur = conn.cursor()

# rows = []
# person_id = 0
# for _, row in df_cleaned.iterrows():
#         if person_id < row["person_id"]:
#             person_id = row["person_id"]
#             genero = 1 if row['Genero'] == 'Masculino' else 0
#             rows.append((
#                 person_id,
#                 genero,
#                 "12345555",
#                 row["Data de Nascimento"],
#                 row["Primeiro Nome"],
#                 row["Último Nome"]
#             ))

# query = """
# INSERT INTO cdmDatabaseSchema.PERSON (
#     person_id, gender_concept_id, person_source_value, birthday, first_name, last_name
# ) VALUES %s
# """

# execute_values(cur, query, rows)
# conn.commit()

# print("Dados PERSON inseridos com sucesso!")


# # Exemplo de inserção na tabela MEASUREMENT
# measurement_concepts = {
#     "SpO2": 1,
#     "NECESSIDADE DE O2": 2,
#     "FREQUÊNCIA CARDIACA": 3,
#     "TA Sistólica": 4,
#     "TA Diastólica": 5,
#     "TEMPERATURA": 6,
#     "NIVEL DE CONSCIÊNCIA": 7,
#     "DOR": 8,
# }

# measurement_id = 1
# rows = []
# for _, row in df_cleaned.iterrows():
#     for field, concept_id in measurement_concepts.items():
#         rows.append((
#             measurement_id,
#             int(row["person_id"]),
#             concept_id,
#             row[field],
#             row["datetime"]
#         ))
#         measurement_id += 1

# query = """
# INSERT INTO cdmDatabaseSchema.MEASUREMENT (
#     measurement_id, person_id, measurement_concept_id, value_as_number, measurement_datetime
# ) VALUES %s
# """


# execute_values(cur, query, rows)
# conn.commit()

# print("Dados MEASUREMENT inseridos com sucesso!")



# diagnosticos = [
#     "Hipertensão arterial", "Diabetes tipo 2", "Insuficiência cardíaca", "DPOC", "Asma",
#     "Enfarte agudo do miocárdio", "AVC isquémico", "Pneumonia", "Fratura do fémur", "Cancro do pulmão",
#     "Insuficiência renal crónica", "Hepatite C", "Cirrose hepática", "Septicemia", "Hipotiroidismo",
#     "Doença de Alzheimer", "Parkinson", "Lombalgia crónica", "Esquizofrenia", "Transtorno bipolar",
#     "Depressão major", "Anemia ferropriva", "Gastrite aguda", "Úlcera péptica", "Infecção urinária",
#     "COVID-19", "Apneia do sono"
# ]


# primeiras_datas = (
#     df_cleaned.groupby("person_id")["datetime"].min().reset_index()
# )

# rows = []
# for i, row in primeiras_datas.iterrows():
#     condition_occurrence_id = i + 1
#     person_id = row["person_id"]
#     condition_start_date = row["datetime"].date()  
#     diagnostico = random.choice(diagnosticos)

#     rows.append((
#         condition_occurrence_id,
#         person_id,
#         condition_start_date,
#         diagnostico
#     ))


# query = """
# INSERT INTO cdmDatabaseSchema.CONDITION_OCCURRENCE (
#     condition_occurrence_id,
#     person_id,
#     condition_start_date,
#     condition_source_value
# ) VALUES %s
# """

# execute_values(cur, query, rows)
# conn.commit()

# print("Dados CONDITION_OCCURRENCE inseridos com sucesso!")


# queixas = [
#     "Dor abdominal", "Tosse persistente", "Febre alta", "Fadiga extrema",
#     "Dificuldade respiratória", "Vómitos", "Tonturas", "Palpitações"
# ]

# alergias = [
#     "Alergia a penicilina", "Intolerância à lactose", "Alergia a frutos secos",
#     "Alergia a marisco", "Alergia ao pólen", "Alergia a anti-inflamatórios"
# ]

# note_rows = []
# note_id = 1
# note_type_queixa = 1  # Queixas de Entrada
# note_type_alergia = 2  # Alergia


# pessoas_unicas = df_cleaned["person_id"].unique()

# for person_id in pessoas_unicas:
    
#     note_rows.append((
#         note_id,
#         int(person_id), # Para não ter erro de tipo
#         random.choice(queixas), #Adiciona uma queixa ao calhas das acima
#         note_type_queixa
#     ))
#     note_id += 1

#     # Nem todos têm alergias
#     if random.random() < 0.5:
#         note_rows.append((
#             note_id,
#             int(person_id), # Para não ter erro de tipo
#             random.choice(alergias), #Adiciona uma alergia ao calhas das acima
#             note_type_alergia
#         ))
#         note_id += 1

# # Inserir na base de dados
# note_query = """
# INSERT INTO cdmDatabaseSchema.NOTE (
#     note_id, person_id, note_text, note_type_concept_id
# ) VALUES %s
# """
# execute_values(cur, note_query, note_rows)
# conn.commit()

# print("Notas inseridas com sucesso!")


# events = {
#     "DESCOMPENSAÇÃO": 1,
#     "Ativação Médico": 2,
#     "Aumento da Vigilância": 3,
#     "Via Área Ameaçada": 4
# }

# event_id = 1
# rows = []
# for _, row in df_cleaned.iterrows():
#     for field, concept_id in events.items():
#         rows.append((
#             event_id,
#             int(row["person_id"]),
#             concept_id,
#             row[field],
#             row["datetime"]
#         ))
#         event_id += 1

# query = """
# INSERT INTO cdmDatabaseSchema.OBSERVATION (
#     observation_id, person_id, observation_concept_id, value_as_number, observation_datetime
# ) VALUES %s
# """


# execute_values(cur, query, rows)
# conn.commit()

# print("Dados OBSERVATION inseridos com sucesso!")

# # Encontrar o índice da primeira medição por pessoa
# idx_primeiras = df_cleaned.groupby("person_id")["datetime"].idxmin()

# # Usar esses índices para obter as linhas completas (incluindo "Serviço")
# primeiras_datas = df_cleaned.loc[idx_primeiras, ["person_id", "datetime", "Serviço"]].reset_index(drop=True)

# rows = []
# for i, row in primeiras_datas.iterrows():
#     visit_occurrence_id = i + 1
#     person_id = row["person_id"]
#     care_site_id = row["Serviço"]
#     visit_start_datetime = row["datetime"] 

#     rows.append((
#         visit_occurrence_id,
#         person_id,
#         care_site_id,
#         visit_start_datetime
#     ))

# query = """
# INSERT INTO cdmDatabaseSchema.VISIT_OCCURRENCE (
#     visit_occurrence_id,
#     person_id,
#     care_site_id,
#     visit_start_datetime
# ) VALUES %s
# """

# execute_values(cur, query, rows)
# conn.commit()

# print("Dados VISIT_OCCURRENCE inseridos com sucesso!")