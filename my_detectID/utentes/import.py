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

for _, row in df.iterrows():
    for field, concept_id in measurement_concepts.items():
        Measurement.objects.create(
            person_id=row["person_id"],
            measurement_concept_id=concept_id,
            value_as_number=row[field],
            measurement_datetime=row["datetime"]
        )

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
for _, row in first_dates.iterrows():
    ConditionOccurrence.objects.create(
        person_id=row["person_id"],
        condition_start_date=row["datetime"].date(),
        condition_source_value=random.choice(diagnosticos)
    )

print("Diagnósticos inseridos!")

# Tabela NOTE
queixas = ["Dor abdominal", "Tosse persistente", "Febre alta", "Fadiga extrema", "Dificuldade respiratória", "Vómitos", "Tonturas", "Palpitações"]
alergias = ["Alergia a penicilina", "Intolerância à lactose", "Alergia a frutos secos", "Alergia a marisco", "Alergia ao pólen", "Alergia a anti-inflamatórios"]

for person_id in df["person_id"].unique():
    Note.objects.create(
        person_id=person_id,
        note_text=random.choice(queixas),
        note_type_concept_id=1
    )

    if random.random() < 0.5:
        Note.objects.create(
            person_id=person_id,
            note_text=random.choice(alergias),
            note_type_concept_id=2
        )

print("Notas inseridas!")

# Tabela OBSERVATION
events = {
    "DESCOMPENSAÇÃO": 1,
    "Ativação Médico": 2,
    "Aumento da Vigilância": 3,
    "Via Área Ameaçada": 4
}

for _, row in df.iterrows():
    for field, concept_id in events.items():
        Observation.objects.create(
            person_id=row["person_id"],
            observation_concept_id=concept_id,
            value_as_number=row[field],
            observation_datetime=row["datetime"]
        )

print("Observações inseridas!")

# Tabela VISIT_OCCURRENCE
visitas = df.loc[df.groupby("person_id")["datetime"].idxmin(), ["person_id", "datetime", "Serviço"]].reset_index(drop=True)
for _, row in visitas.iterrows():
    VisitOccurrence.objects.create(
        person_id=row["person_id"],
        care_site_id=row["Serviço"],
        visit_start_datetime=row["datetime"]
    )

print("Visitas inseridas!")
