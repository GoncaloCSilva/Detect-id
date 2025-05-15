import pandas as pd
import random
from datetime import datetime
from utentes.models import MeasurementExt, Person, Measurement, ConditionOccurrence, Note, Observation, VisitOccurrence, PersonExt

file_path = "detectid.csv"
df = pd.read_csv(file_path)

# Processamento dos tipos
numeric_cols = df.select_dtypes(include='number').columns
df[numeric_cols] = df[numeric_cols].fillna(df[numeric_cols].mean())

# NIVEL DE CONSCIÊNCIA como inteiro com média preenchida
df["Nível de Consciência"] = pd.to_numeric(df["Nível de Consciência"], errors='coerce')
media_nivel = int(df["Nível de Consciência"].mean().round())
df["Nível de Consciência"].fillna(media_nivel, inplace=True)

# Criar datetime auxiliar para ordenação e cálculo
df["datetime"] = pd.to_datetime(df["Dia de Medição"] + " " + df["Hora de Medição"], dayfirst=True, errors="coerce")

# Extrair ID da pessoa
df["person_id"] = df["Pessoa"].str.extract(r"(\d+)").astype(int)

# Calcular tempo em horas desde a 1ª medição da pessoa
df.sort_values(by=["person_id", "datetime"], inplace=True)
df["Tempo"] = df.groupby("person_id")["datetime"].transform(lambda x: (x - x.min()).dt.total_seconds() / 3600)
df["Tempo"] = df["Tempo"].round(2)

# Manter a Data de Nascimento no formato original (não transformar para datetime.date)
# Garante que a coluna é string e tem o formato correto
df["Data de Nascimento"] = df["Data de Nascimento"].astype(str).str.strip()

# Guardar novo CSV com a coluna "Tempo"
df.to_csv("detectid_com_tempo.csv", index=False)

df["Dia de Medição"] = df["Dia de Medição"].astype(str)
df["Hora de Medição"] = df["Hora de Medição"].astype(str)
df["Data de Nascimento"] = pd.to_datetime(df["Data de Nascimento"], format='%d/%m/%Y', errors='coerce').dt.date

# Inserir dados na tabela Person
pessoas_adicionadas = set()
for _, row in df.iterrows():
    pid = row["person_id"]
    if pid not in pessoas_adicionadas:
        genero = 1 if row['Genero'] == 'Masculino' else 0
        person_ext = PersonExt(
            gender_concept_id=genero,
            person_source_value="12345555",
            birthday=row["Data de Nascimento"],
            first_name=row["Primeiro Nome"],
            last_name=row["Último Nome"]
        )
        person_ext.save()
        pessoas_adicionadas.add(pid)

print("Pessoas inseridas!")

# Tabela MEASUREMENT
measurement_concepts = {
    "SpO2": 1,
    "Necessidade de O2": 2,
    "Frequência Cardíaca": 3,
    "TA Sistólica": 4,
    "TA Diastólica": 5,
    "Temperatura": 6,
    "Nível de Consciência": 7,
    "Dor": 8,
}

parametros = {
    1: [90, 95, 98],
    2: [1, 2, 3],
    3: [60, 100, 120],
    4: [100.5, 119.5, 134.5],
    5: [60, 80, 90],
    6: [35.5, 37.5, 38.5],
    7: [8, 13, 15],
    8: [1,2,3],
    }

for _, row in df.iterrows():
    for field, concept_id in measurement_concepts.items():
        MeasurementExt.objects.create(
            person_id=row["person_id"],
            measurement_concept_id=concept_id,
            value_as_number=row[field],
            measurement_datetime=row["datetime"],
            range_low = parametros[concept_id][0],
            range_high = parametros[concept_id][2],
            range_mid = parametros[concept_id][1],
            time_field= row["Tempo"]
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
    "Descompensação": 1,
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
