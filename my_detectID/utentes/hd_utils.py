import os
from pathlib import Path
import random
from django.conf import settings
from django.db import connection
import numpy as np
import pandas as pd
from lifelines import KaplanMeierFitter
from sklearn.model_selection import train_test_split
from sksurv.ensemble import RandomSurvivalForest
from sksurv.util import Surv
from sklearn.preprocessing import StandardScaler
import pickle
import yaml
from .models import ConditionOccurrence, Measurement, MeasurementExt, Note, Observation, Person, PersonExt, VisitOccurrence, CareSite


# Stores the CSV data
_csv_data = None

# Dictionary to store all Kaplan Meir models
MODELOS_KM = {}

# Dictionary to store all Random Surival Forest Models
MODELOS_RSF = {}

# Dictionary to store all the information about the parameters
# Name, Abbreviation, Full Name, Thresholds, Unit of Measurement
PARAMETERS = {}

# Dictionary that stores all events and their IDs
EVENTS = {}

# The yaml configuration file
CONFIG = None

# Signals the model thats being used 
# 1-> KM 
# 2-> RSF
CURRENT_MODEL = 1 

def load_config():
    """
    @brief Loads the application configuration from a .yaml file.

    This function checks if the global CONFIG variable has already been set.
    If not, it reads the 'config/hd_config.yaml' file and stores the parsed content
    in the CONFIG variable using PyYAML.

    @return dict The loaded configuration dictionary.
    """
    global CONFIG
    if CONFIG is None:
        config_path = Path(settings.BASE_DIR) / 'config' / 'hd_config.yaml'
        with open(config_path, "r", encoding="utf-8") as file:
            CONFIG = yaml.safe_load(file)
    return CONFIG

def get_parameters():
    """
    @brief Retrieves the clinical parameters defined in the configuration file.

    This function loads the configuration using `load_config()` (if the parameters weren't already loaded),
    and extracts the list of clinical parameters from the "parameters" section. Each
    parameter is assigned a unique integer ID and stored in the global `PARAMETERS`
    dictionary in the format:
    (name, abbreviated name, full name, thresholds, unit of measurement).

    The function caches the result in the global `PARAMETERS` variable to avoid
    redundant file reads.

    @return dict A dictionary mapping parameter IDs to their metadata tuples.
    """
    global PARAMETERS
    
    if not PARAMETERS:
        config = load_config()
        parameters = config["parameters"]
        id = 1
        for param in parameters:
            PARAMETERS[id] = (param["name"], param["abv_name"], param["full_name"], param["thresholds"], param["unit_measurement"])
            id += 1
    
    return PARAMETERS
        
def get_events():
    """
    @brief Retrieves the clinical events defined in the configuration file.

    This function loads the configuration using `load_config()` (if the event weren't already loaded),
    and extracts the list of clinical events from the "events" section. Each event is 
    assigned a unique integer ID and stored in the global `EVENTS` dictionary.

    The function caches the result in the global `EVENTS` variable to avoid
    repeated file reads and parsing.

    @return dict A dictionary mapping event IDs to their corresponding event names or definitions.
    """
    global EVENTS
    
    if not EVENTS:
        config = load_config()
        events = config["events"]
        id = 1
        for event in events:
            EVENTS[id] = event
            id += 1
    
    return EVENTS

def get_param_group(param_id, value, group_count):
    """
    @brief Determines the clinical parameter group based on the provided value and thresholds.

    This function compares a given `value` of a clinical parameter (`param_id`) 
    against a list of threshold values defined in the configuration file. It returns a group number 
    based on the value's position within the defined ranges.
    The first threshold is group number 1.
    The second threshold is group number 2.
    And so on.

    @param param str: The internal id of the clinical parameter (e.g., 1 -> "SpO2").
    @param value float: The measured value to classify.
    @param group_count int: The total number of defined groups (e.g., 4).

    @return int or None: Returns the group index (1-based) if the value falls within a range,
                         or the highest group number if it exceeds all thresholds.
                         Returns None if the value is NaN.
    """
    global PARAMETERS
    if pd.isna(value):
        return None
    
    for id,(name,abvName,fullName,thresholds,unitMeasurement) in PARAMETERS.items():
        for i in range(0, group_count-1):
            if id == param_id:
                if value >= thresholds[i]:
                    return i + 1
    return group_count

def getCurrentModel():
    """
    @brief Retrieves the information about the current model that is being used.

    @return Any: Flag that signals the currently used model object.
    """
    global CURRENT_MODEL
    return CURRENT_MODEL

def setCurrentModel(model):
    """
    @brief Sets the information about the current model.

    This function is used to set the flag that signals what model is being used

    @param model int: 1 or 2
    """
    global CURRENT_MODEL
    CURRENT_MODEL = model

def predict_survival(model, time):
    """
    @brief Predicts the survival probability at a specific time using either a Kaplan-Meier (KM) or 
           Random Survival Forest (RSF) model.

    @param model: The trained survival model. 
                  - For KM, this is an instance with a `predict(time)` method.
                  - For RSF, this is expected to be a tuple or list-like object where model[0].x and model[0].y 
                    define the survival function as discrete time-probability pairs.
    @param time (float): The time point at which the survival probability should be predicted.

    @return float: The estimated survival probability at the given time.
                   If the RSF interpolation fails, a default value of 0.5 is returned.
    """
    if CURRENT_MODEL == 1:  # KM
        return model.predict(time)
    else:  # RSF
        try:
            prob = np.interp(time, model[0].x, model[0].y)
        except:
            prob = 0.5

        return prob
    
def trainModels():
    """
    @brief Loads or trains Kaplan-Meier (KM) and Random Survival Forest (RSF) models for each clinical parameter 
           and clinical event combination. Also trains global models using all parameters.

    This function either:
    - Loads pre-trained models from pickle files if they exist and training is disabled in the config (`train_models == 0`), or
    - Trains new models from CSV clinical data if models do not exist or training is enabled.

    For each parameter and clinical event, the function:
    - Divides the data into risk groups based on predefined thresholds.
    - Trains one KM model per group.
    - Trains one RSF model per group using survival data.

    Global KM and RSF models (using all parameters and all groups) are also trained.

    Trained models are saved as pickle files for future use.

    @global _csv_data: Stores the loaded and preprocessed clinical data.
    @global MODELOS_KM: Dictionary to store KM models for each parameter-event-group.
    @global MODELOS_RSF: Dictionary to store RSF models for each parameter-event-group.
    @global PARAMETERS: Dictionary of parameters loaded from the YAML config.
    @global EVENTS: Dictionary of events loaded from the YAML config.

    @return pd.DataFrame: The preprocessed clinical data used to train the models.
    """
    global _csv_data, MODELOS_KM,MODELOS_RSF,PARAMETERS, EVENTS
    config = load_config()

    train_models = config["train_models"]

    # If the files exist and training is not enabled in the configuration file, the load pre-trained models
    pickle_dir = Path(settings.BASE_DIR) / 'pickle'
    rsf_path = pickle_dir / 'rsf_modelos.pkl'
    km_path = pickle_dir / 'km_modelos.pkl'

    if rsf_path.exists() and km_path.exists() and train_models == 0:
        with open(rsf_path, "rb") as f:
            MODELOS_RSF = pickle.load(f)
        with open(km_path, "rb") as f:
            MODELOS_KM = pickle.load(f)

        _csv_data = getCSV()
        _csv_data['datetime'] = pd.to_datetime(_csv_data['datetime'])
        _csv_data = _csv_data.sort_values(by=["person_id", "datetime"])

    # If the training is enabled or one of the files don't exist, then the models will be trained
    else: 

        _csv_data = getCSV()
        _csv_data['datetime'] = pd.to_datetime(_csv_data['datetime'])
        _csv_data = _csv_data.sort_values(by=["person_id", "datetime"])

        events = get_events()
        parameters = get_parameters()
   
        group_count = load_config()["general_settings"]["num_thresholds"]
        groups = list(range(1, group_count + 1))

        #Train KM and RSF models for every parameter-event-group
        for param_id,(param_name,param_abvName,param_fullName,param_thresholds,param_unit) in parameters.items():
            MODELOS_KM[param_id] = {}
            MODELOS_RSF[param_id] = {}
            for event_id,event_name in events.items():
                MODELOS_KM[param_id][event_id] = {}
                MODELOS_RSF[param_id][event_id] = {}

                for group in groups:
                    # Filter the data for this group
                    grupo_df = _csv_data[_csv_data[param_name].apply(lambda x: get_param_group(param_id, x ,group_count)) == group]
                    if not grupo_df.empty:

                        #### KaplanMeier ####
                        kmf = KaplanMeierFitter()
                        kmf.fit(grupo_df["Tempo"], event_observed=grupo_df[event_name], label=f"{param_name}_{group}_{event_name}")
                        MODELOS_KM[param_id][event_id][group] = kmf

                        #### Random Surival Forest ####
                        X = _csv_data[[param_name]]
                        y = Surv.from_dataframe("Evento", "Tempo", _csv_data)

                        # Normalize 
                        scaler = StandardScaler()
                        X_scaled = scaler.fit_transform(X)

                        # Split train/test/validation
                        X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.3, random_state=33)
                        X_val_train, X_val_test, y_val_train, y_val_test = train_test_split(X_train, y_train, test_size=0.3, random_state=33)

                        # Train model
                        rsf = RandomSurvivalForest()
                        
                        rsf.fit(X_val_train, y_val_train)
                        rsf.fit(X_train, y_train)

                        rsf = rsf.predict_survival_function(X_test[:1])

                        MODELOS_RSF[param_id][event_id][group] = rsf

        ### Global models ###

        ## KM ##
        kmf = KaplanMeierFitter()
        kmf.fit(_csv_data["Tempo"], _csv_data["Evento"])
        MODELOS_KM["global"] = kmf

        ## RSF ##
        param_names = [name for name, _, _, _, _ in get_parameters().values()]
        X = _csv_data[param_names]
        y = Surv.from_dataframe("Evento", "Tempo", _csv_data)

        # Normalize
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)

        # Split train/test/validation
        X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.3, random_state=33)
        X_val_train, X_val_test, y_val_train, y_val_test = train_test_split(X_train, y_train, test_size=0.3, random_state=33)


        # Train model
        rsf = RandomSurvivalForest()

        rsf.fit(X_val_train, y_val_train)
        rsf.fit(X_train, y_train)

        rsf = rsf.predict_survival_function(X_test[:1])

        MODELOS_RSF["global"] = rsf

        # Save the models in the pickle files
        with open(rsf_path, "wb") as f:
            pickle.dump(MODELOS_RSF,f)
        with open(km_path, "wb") as f:
            pickle.dump(MODELOS_KM,f)

    return _csv_data

def get_model(param_id, value, evento_id=1):
    """
    @brief Returns the trained survival model (KM or RSF) for a given parameter value and event.
    
    The function determines the appropriate risk group for the parameter value using its threshold configuration,
    and then retrieves the corresponding trained model (KM or RSF) based on the selected model type (`CURRENT_MODEL`).

    Special case: For parameter ID 8, the group is fixed to 2.
    because there is not enough data for group 1

    @param param_id: ID of the clinical parameter (e.g., 1 for 'SpO2').
    @param value: The value of the parameter to classify into a group.
    @param evento_id: (Optional) ID of the clinical event to retrieve the model for (default is 1).

    @return: The corresponding trained KM or RSF model object.
    """

    (name, abv_name,fullname, thresholds, unitMeasurement) = PARAMETERS[param_id]
    config = load_config()
    group_count = config["general_settings"]["num_thresholds"]
    group = None
    
    if param_id == 8:
        group = 2
    else:
        for i in range(0, group_count-1):
                if value >= thresholds[i]:
                    group = i + 1
                    break

    if group is None:
        group = group_count
    
    if CURRENT_MODEL == 1:
        return MODELOS_KM.get(param_id, {}).get(evento_id, {}).get(group, None)
    else:
        return MODELOS_RSF.get(param_id, {}).get(evento_id, {}).get(group, None)

def get_global_model():
    """
    @brief Returns the global trained survival model based on the current model type.

    This function retrieves the model trained on the entire dataset, rather than a specific parameter or group.
    It selects between KM or RSF models based on the value of the global variable CURRENT_MODEL.

    @return: The global KM or RSF model object.
    """
    if CURRENT_MODEL == 1:
        return MODELOS_KM.get("global") 
    else:
        return MODELOS_RSF.get("global") 
    
def changeCSV(csv_file):
    """
    @brief Replaces the existing 'detectid.csv' file, deletes existing model files, clears the database, and imports new data.
    @param csv_file: Uploaded CSV file object.
    
    This function performs the following steps:
    1. Saves the uploaded CSV file to the base directory as 'detectid.csv'.
    2. Deletes all pickle files (*.pkl) from the 'pickle' directory, effectively removing saved models.
    3. Calls functions to clear the database and import data from the new CSV.
    """

    # Save new CSV File
    csv_path = os.path.join(settings.BASE_DIR, "detectid.csv")

    with open(csv_path, 'wb+') as destination:
        for chunk in csv_file.chunks():
            destination.write(chunk)

    # Deletes the pickle files
    pkl_dir = os.path.join(settings.BASE_DIR, "pickle")  
    if os.path.exists(pkl_dir):
        for file in os.listdir(pkl_dir):
            if file.endswith(".pkl"):
                os.remove(os.path.join(pkl_dir, file))

    # Clears the DataBase with the old data
    deleteData()
    # Fills the DataBase with the new data
    importData()

def getCSV(file_path = "detectid.csv", importBD=False):
    """
    @brief Loads and preprocesses the CSV data for survival analysis.
    @param file_path: Path to the CSV file to load (default "detectid.csv").
    @param importBD: Boolean flag indicating if the data is being imported into the database (default False).
    @return: A pandas DataFrame with cleaned and processed data, including calculated time since first measurement.

    This function performs the following steps:
    - Reads the CSV file into a DataFrame.
    - Fills missing numeric values with column means or parameter-specific means.
    - Converts measurement date and time columns into a single datetime column.
    - Extracts person IDs and calculates time (in hours) since each person's first measurement.
    - Fills missing event columns with zero.
    - Optionally filters to keep only the last measurement per person when importBD is False.
    - Saves a new CSV file with an additional "Tempo" column.
    """
    file_path = Path(settings.BASE_DIR) / file_path
    df = pd.read_csv(file_path)

    # Process numeric columns: fill missing values with the rounded mean of each column
    numeric_cols = df.select_dtypes(include='number').columns
    df[numeric_cols] = df[numeric_cols].fillna(round(df[numeric_cols].mean(),2))

    # Fill missing values in "Evento" column with 0
    df["Evento"] = df["Evento"].fillna(0)

    parameters = get_parameters()

    # For each clinical parameter, convert to numeric, fill missing with rounded mean
    for param_id, (para_name, abv_name,fullname, thresholds, unitMeasurement) in parameters.items():
        df[para_name] = pd.to_numeric(df[para_name], errors='coerce')
        media_nivel = int(df[para_name].mean().round())
        df[para_name].fillna(media_nivel, inplace=True)

    # Create auxiliary datetime column for sorting and calculation
    df["datetime"] = pd.to_datetime(df["Dia de Medição"] + " " + df["Hora de Medição"], dayfirst=True, errors="coerce")

    # Extract person ID as integer
    df["person_id"] = df["Pessoa"].astype(int)

    # Calculate time in hours since the first measurement for each person
    df.sort_values(by=["person_id", "datetime"], inplace=True)
    df["Tempo"] = df.groupby("person_id")["datetime"].transform(lambda x: (x - x.min()).dt.total_seconds() / 3600)
    df["Tempo"] = df["Tempo"].round(2)
    df["Tempo"].fillna(df["Tempo"].median(), inplace=True)

    # Keep the birth date in original format (do not convert to datetime.date)
    # Ensure the column is string and properly formatted
    df["Data de Nascimento"] = df["Data de Nascimento"].astype(str).str.strip()

    df["Dia de Medição"] = df["Dia de Medição"].astype(str)
    df["Hora de Medição"] = df["Hora de Medição"].astype(str)
    df["Data de Nascimento"] = pd.to_datetime(df["Data de Nascimento"], format='%d/%m/%Y', errors='coerce').dt.date

    events = get_events()

    # Fill missing values in event columns with 0
    for event_id, event_name in events.items():
        df[event_name].fillna(0, inplace=True)

    # Keep only the last measurement per person if importBD is False
    if importBD is False:
        df = df.groupby("person_id", as_index=False).last()

    return df

def importData():
    """
    @brief Imports clinical data from a CSV file into various database tables.

    This function performs data import and insertion into multiple tables of the clinical data model,
    including PersonExt, MeasurementExt, ConditionOccurrence, Note, Observation, CareSite, and VisitOccurrence.
    It handles missing data by generating synthetic values for columns that may not exist in the CSV,
    such as primary diagnoses, complaints, and allergies.

    Main steps:
    - Load configuration file (parameters and events).
    - Read clinical data CSV file.
    - Insert unique patients into the PersonExt table.
    - Build a measurement concepts dictionary from configuration and insert data into MeasurementExt.
    - Insert diagnoses into ConditionOccurrence table with fallback to random diagnoses if missing.
    - Insert complaints and allergies into Note table, using random values if columns are missing.
    - Insert clinical events into the Observation table.
    - Insert care site information into CareSite table.
    - Insert visits into VisitOccurrence table.

    @param None

    @return None
    """
    # Load configuration file
    config = load_config()

    # Read clinical data CSV file (importBD=True specifies the source file)
    df = getCSV(importBD=True)

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
                

    # Insert care sites into CareSite table
    service_names={1: "Urgência", 2: "Internamento", 3: "UCI"}

    services = df["Serviço"].unique()
    for service in services:
        CareSite.objects.create(
            care_site_id=service,
            care_site_name=service_names.get(service)
        )

    # Insert visits into VisitOccurrence table
    visits = df.loc[df.groupby("person_id")["datetime"].idxmin(), ["person_id", "datetime", "Serviço"]].reset_index(drop=True)
    for _, row in visits.iterrows():
        VisitOccurrence.objects.create(
            person_id=row["person_id"],
            care_site_id=row["Serviço"],
            visit_start_datetime=row["datetime"]
        )

def deleteData():
    """
    @brief Deletes all clinical data from the database tables.

    This function performs a cascade of deletions in the following order:
    - Deletes all measurements (Measurement and MeasurementExt).
    - Deletes all condition occurrences.
    - Deletes all notes.
    - Deletes all observations.
    - Deletes all visit occurrences.
    - Deletes all care sites (use with caution if shared with other data).
    - Deletes all persons (Person and PersonExt).

    After deletions, it resets the primary key sequences for tables to start from 1.

    @param None
    @return None
    """

    # Delete all measurements
    Measurement.objects.all().delete()
    MeasurementExt.objects.all().delete()

    # Delete all condition occurrences
    ConditionOccurrence.objects.all().delete()

    # Delete all notes
    Note.objects.all().delete()

    # Delete all observations
    Observation.objects.all().delete()

    # Delete all visits
    VisitOccurrence.objects.all().delete()

    # Delete all care sites
    CareSite.objects.all().delete()

    # Finally, delete all persons
    Person.objects.all().delete()
    PersonExt.objects.all().delete()

    def reset_sequence(table_name, pk_column):
        """
        @brief Resets the primary key sequence for a PostgreSQL table.

        @param table_name: Name of the table (string)
        @param pk_column: Name of the primary key column (string)
        """
        seq_name = f"{table_name}_{pk_column}_seq"
        with connection.cursor() as cursor:
            cursor.execute(f"ALTER SEQUENCE {seq_name} RESTART WITH 1;")

    # Reset sequences for affected tables
    reset_sequence('person', 'person_id')