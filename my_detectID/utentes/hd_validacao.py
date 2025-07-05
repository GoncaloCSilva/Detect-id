# Load configuration file
import random

import pandas as pd
from utentes.hd_utils import getCSV, load_config
from utentes.models import CareSite, ConditionOccurrence, MeasurementExt, Note, Observation, PersonExt, VisitOccurrence


config = load_config()

# Read clinical data CSV file (importBD=True specifies the source file)
df = getCSV("validacao.csv",importBD=True)
print(df)
# Insert data into PersonExt table, avoiding duplicates
addedPacients = set()

for _, row in df.iterrows():
    personID = row["person_id"]
    if personID not in addedPacients:
        genero = 1 if row['Genero'] == 'Masculino' else 0
        person_ext = PersonExt(
            gender_concept_id=genero,
            person_source_value="12345555",
            birthday=row["Data de Nascimento"],
            first_name=row["Primeiro Nome"],
            last_name=row["Último Nome"]
        )

        person_ext.save()

        addedPacients.add(personID)
print("INSERI PESSOAS")
# Build measurement concepts dictionary from configuration
parameters = config["parameters"]

id = 1
measurement_concepts = {}
for param in parameters:
    measurement_concepts[id] = (param["name"],param["abv_name"],param["full_name"] ,param["thresholds"],param["unit_measurement"])
    id +=1

# Insert measurements into Measurement table
for _, row in df.iterrows():
    for concept_id, (name, abv_name,fullname, thresholds, unitMeasurement) in measurement_concepts.items():
        MeasurementExt.objects.create(
            person_id=row["person_id"],
            measurement_concept_id=concept_id,
            value_as_number=row[name],
            measurement_datetime=row["datetime"],
            range_low = thresholds[0],
            range_high = thresholds[1]
        )
print("INSERI MEDIÇÕES")
# Insert condition occurrences with fallback to random diagnoses if missing
diagnostics = [
    "Hipertensão arterial", "Diabetes tipo 2", "Insuficiência cardíaca", "DPOC", "Asma",
    "Enfarte agudo do miocárdio", "AVC isquémico", "Pneumonia", "Fratura do fémur", "Cancro do pulmão",
    "Insuficiência renal crónica", "Hepatite C", "Cirrose hepática", "Septicemia", "Hipotiroidismo",
    "Doença de Alzheimer", "Parkinson", "Lombalgia crónica", "Esquizofrenia", "Transtorno bipolar",
    "Depressão major", "Anemia ferropriva", "Gastrite aguda", "Úlcera péptica", "Infecção urinária",
    "COVID-19", "Apneia do sono"
]

first_dates = df.groupby("person_id")["datetime"].min().reset_index()
has_diag_col = "Diagnóstico Principal" in df.columns

for _, row in first_dates.iterrows():
    if has_diag_col:
        # Se existir, tentar obter o diagnóstico no df original (precisas fazer merge para isso)
        diag_row = df[(df["person_id"] == row["person_id"]) & (df["datetime"] == row["datetime"])]
        if not diag_row.empty and pd.notna(diag_row.iloc[0]["Diagnóstico Principal"]):
            diagnostic = diag_row.iloc[0]["Diagnóstico Principal"]
        else:
            diagnostic = random.choice(diagnostics)
    else:
        diagnostic = random.choice(diagnostics)

    ConditionOccurrence.objects.create(
        person_id=row["person_id"],
        condition_start_date=row["datetime"].date(),
        condition_source_value=diagnostic
    )
print("INSERI DIAGNOSTICOS")
# Insert notes into Note table (complaints and allergies), generating random values if columns are missing
complaints = ["Dor abdominal", "Tosse persistente", "Febre alta", "Fadiga extrema", "Dificuldade respiratória", "Vómitos", "Tonturas", "Palpitações"]

allergies = ["Alergia a penicilina", "Intolerância à lactose", "Alergia a frutos secos", "Alergia a marisco", "Alergia ao pólen", "Alergia a anti-inflamatórios"]
has_complaint_col = "Queixas de Entrada" in df.columns
has_allergy_col = "Alergias" in df.columns

for person_id in df["person_id"].unique():
    if has_complaint_col:
        complaint_row = df[df["person_id"] == person_id]
        if not complaint_row.empty and pd.notna(complaint_row.iloc[0]["Queixas de Entrada"]):
            complaint = complaint_row.iloc[0]["Queixas de Entrada"]
        else:
            complaint = random.choice(complaints)
    else:
        complaint = random.choice(complaints)

    Note.objects.create(
        person_id=person_id,
        note_text=complaint,
        note_type_concept_id=1
    )

    if has_allergy_col:
        allergy_row = df[df["person_id"] == person_id]
        if not allergy_row.empty and pd.notna(allergy_row.iloc[0]["Alergias"]):
            allergy = allergy_row.iloc[0]["Alergias"]
            Note.objects.create(
                person_id=person_id,
                note_text=allergy,
                note_type_concept_id=2
            )
        else:
            allergy = random.choice(allergies)
            if random.random() < 0.5:
                Note.objects.create(
                    person_id=person_id,
                    note_text=allergy,
                    note_type_concept_id=2
                )
    else:
        allergy = random.choice(allergies)
        if random.random() < 0.5:
            Note.objects.create(
                person_id=person_id,
                note_text=allergy,
                note_type_concept_id=2
            )
print("INSERI NOTAS")
# Insert clinical events into Observation table
events_config = config["events"]
id = 1
events = {}
for event in events_config:
    events[id] = event
    id+=1

for _, row in df.iterrows():
    for concept_id, name in events.items():
        if row[name] == 1:
            Observation.objects.create(
                person_id=row["person_id"],
                observation_concept_id=concept_id,
                value_as_number=row[name],
                observation_datetime=row["datetime"]
            )
            
print("INSERI EVENTOS")

# Insert visits into VisitOccurrence table
visits = df.loc[df.groupby("person_id")["datetime"].idxmin(), ["person_id", "datetime", "Serviço"]].reset_index(drop=True)
for _, row in visits.iterrows():
    VisitOccurrence.objects.create(
        person_id=row["person_id"],
        care_site_id=1,
        visit_start_datetime=row["datetime"]
    )
print("INSERI ENTRADAS")