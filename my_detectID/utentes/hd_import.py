import pandas as pd
import random
from datetime import datetime
from utentes.hd_utils import getCSV, load_config
from utentes.models import MeasurementExt, Person, Measurement, ConditionOccurrence, Note, Observation, VisitOccurrence, PersonExt
import yaml

def importData():
    # Carregar o ficheiro de configuração
    config = load_config()

    df = getCSV(importBD=True)
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
            print(f"Pessoa -> {person_ext.first_name} {person_ext.last_name} (ID: {person_ext.person_id})")
            pessoas_adicionadas.add(pid)

    print("Pessoas inseridas!")

    parameters = config["parameters"]
    id = 1
    measurement_concepts = {}
    for param in parameters:
        measurement_concepts[id] = (param["name"],param["abv_name"],param["full_name"] ,param["thresholds"],param["unit_measurement"])
        id +=1

    # Tabela MEASUREMENT
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
                print(f"Observação {name} inserida para o utente {row['person_id']} com o valor {row[name]}")
                

    print("Observações inseridas!")

    # Tabela Care Site
    from utentes.models import CareSite

    nomes_servicos={1: "Urgência", 2: "Internamento", 3: "UCI"}

    servicos = df["Serviço"].unique()
    for servico in servicos:
        CareSite.objects.create(
            care_site_id=servico,
            care_site_name=nomes_servicos.get(servico)
        )

    # Tabela VISIT_OCCURRENCE
    visitas = df.loc[df.groupby("person_id")["datetime"].idxmin(), ["person_id", "datetime", "Serviço"]].reset_index(drop=True)
    for _, row in visitas.iterrows():
        VisitOccurrence.objects.create(
            person_id=row["person_id"],
            care_site_id=row["Serviço"],
            visit_start_datetime=row["datetime"]
        )

    print("Visitas inseridas!")

