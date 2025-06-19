import os
import numpy as np
import pandas as pd
from lifelines import KaplanMeierFitter
from sklearn.model_selection import train_test_split
from sksurv.ensemble import RandomSurvivalForest
from sksurv.util import Surv
from sklearn.preprocessing import StandardScaler
import pickle
import yaml


_csv_data = None

MODELOS_KM = {}

MODELOS_RSF = {}

# Dictionary to hold all the information about the parameters
# Name, Abbreviation, Full Name, Thresholds, Unit of Measurement
PARAMETERS = {}

EVENTS = {}

LIMIARES = {
        1: ("SpO2", [90, 98]),
        2: ("Necessidade de O2", [0,1]),
        3: ("Frequência Cardíaca", [60, 99]),
        4: ("TA Sistólica", [100, 130]),
        5: ("TA Diastólica", [60,90]),
        6: ("Temperatura", [35, 38]),
        7: ("Nível de Consciência", [8, 15]),
        8: ("Dor", [0,1]),
        }   

CONFIG = None

CURRENT_MODEL = 1 # 1-> KM 2-> RSF

def load_config():
    global CONFIG
    if CONFIG is None:
        with open("config/hd_config.yaml", "r", encoding="utf-8") as file:
            CONFIG = yaml.safe_load(file)
    return CONFIG

def get_parameters():
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
    global EVENTS
    
    if not EVENTS:
        config = load_config()
        events = config["events"]
        id = 1
        for event in events:
            EVENTS[id] = event
            id += 1
    
    return EVENTS

def get_param_group(param, value, group_count):
    global PARAMETERS
    if pd.isna(value):
        return None
    
    for id,(name,abvName,fullName,thresholds,unitMeasurement) in PARAMETERS.items():
        for i in range(0, group_count-1):
            if name == param:
                if value >= thresholds[i]:
                    return i + 1
    return group_count

def getCurrentModel():
    global CURRENT_MODEL
    return CURRENT_MODEL

def setCurrentModel(model):
    global CURRENT_MODEL
    CURRENT_MODEL = model

def predict_survival(model,time):
    """
    @brief Predict survival probability at a given time using either KM or RSF.
    @param model: KM or RSF model
    @param X: Input data (may be ignored by KM)
    @param time: Time at which to predict survival
    @return: Estimated survival probability at the given time
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
    global _csv_data, MODELOS_KM,MODELOS_RSF,PARAMETERS, EVENTS
    if os.path.exists("./pickle/rsf_modelos.pkl") and os.path.exists("./pickle/km_modelos.pkl"):
    
        print("A carregar modelos...")
        with open("./pickle/rsf_modelos.pkl", "rb") as f:
            MODELOS_RSF = pickle.load(f)
        with open("./pickle/km_modelos.pkl", "rb") as f:
            MODELOS_KM = pickle.load(f)
        _csv_data = getCSV()
        _csv_data['datetime'] = pd.to_datetime(_csv_data['datetime'])
        _csv_data = _csv_data.sort_values(by=["person_id", "datetime"])
    else:
        print("A Carregar o ficheiro CSV...")

        _csv_data = getCSV()
        _csv_data['datetime'] = pd.to_datetime(_csv_data['datetime'])
        _csv_data = _csv_data.sort_values(by=["person_id", "datetime"])

        events = get_events()
        parameters = get_parameters()
   

        group_count = load_config()["general_settings"]["num_thresholds"]
        groups = list(range(1, group_count + 1))

        #Treinar os Modelos KM
        for param_id,(param_name,param_abvName,param_fullName,param_thresholds,param_unit) in parameters.items():
            MODELOS_KM[param_id] = {}
            MODELOS_RSF[param_id] = {}
            for event_id,event_name in events.items():
                MODELOS_KM[param_id][event_id] = {}
                MODELOS_RSF[param_id][event_id] = {}

                for group in groups:
                    # Filtrar os dados para este grupo
                    grupo_df = _csv_data[_csv_data[param_name].apply(lambda x: get_param_group(param_name, x ,group_count)) == group]
                    if not grupo_df.empty:

                        #### KaplanMeier ####
                        kmf = KaplanMeierFitter()
                        kmf.fit(grupo_df["Tempo"], event_observed=grupo_df[event_name], label=f"{param_name}_{group}_{event_name}")
                        MODELOS_KM[param_id][event_id][group] = kmf

                        #### Random Surival Forest ####
                        X = _csv_data[[param_name]]
                        y = Surv.from_dataframe("Evento", "Tempo", _csv_data)

                        # Normalizar
                        scaler = StandardScaler()
                        X_scaled = scaler.fit_transform(X)

                        # Dividir treino/teste
                        X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.3, random_state=33)
                        X_val_train, X_val_test, y_val_train, y_val_test = train_test_split(X_train, y_train, test_size=0.3, random_state=33)


                        # Treinar modelo
                        rsf = RandomSurvivalForest()
                        
                        rsf.fit(X_val_train, y_val_train)

                        rsf.fit(X_train, y_train)
                        rsf = rsf.predict_survival_function(X_test[:1])

                        MODELOS_RSF[param_id][event_id][group] = rsf

        kmf = KaplanMeierFitter()
        kmf.fit(_csv_data["Tempo"], _csv_data["Evento"])
        MODELOS_KM["global"] = kmf

        param_names = [name for name, _, _, _, _ in get_parameters().values()]
        X = _csv_data[param_names]
        y = Surv.from_dataframe("Evento", "Tempo", _csv_data)

        # Normalizar
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)

        # Dividir treino/teste
        X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.3, random_state=33)
        X_val_train, X_val_test, y_val_train, y_val_test = train_test_split(X_train, y_train, test_size=0.3, random_state=33)


        # Treinar modelo
        rsf = RandomSurvivalForest()


        rsf.fit(X_val_train, y_val_train)

        rsf.fit(X_train, y_train)
        rsf = rsf.predict_survival_function(X_test[:1])

        MODELOS_RSF["global"] = rsf


        with open("./pickle/rsf_modelos.pkl", "wb") as f:
            pickle.dump(MODELOS_RSF,f)
        with open("./pickle/km_modelos.pkl", "wb") as f:
            pickle.dump(MODELOS_KM,f)

    return _csv_data

def getLimiares():
    global LIMIARES
    return LIMIARES

def get_model(param_id, value, evento_id=1):
    """
    @brief: Devolve o modelo Kaplan-Meier treinado para o parâmetro e grupo fornecido.
    @param parametro: ID do parâmetro clínico (ex: 1 -> 'SpO2')
    @param valor: Valor da medicao do parametro
    @return: Objeto KaplanMeierFitter treinado ou None
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
    if CURRENT_MODEL == 1:
        return MODELOS_KM.get("global") 
    else:
        return MODELOS_RSF.get("global") 


def getCSV(file_path = "detectid.csv", importBD=False):

    df = pd.read_csv(file_path)

    # Processamento dos tipos
    numeric_cols = df.select_dtypes(include='number').columns
    df[numeric_cols] = df[numeric_cols].fillna(df[numeric_cols].mean())

    parameters = get_parameters()

    for param_id, (para_name, abv_name,fullname, thresholds, unitMeasurement) in parameters.items():
        df[para_name] = pd.to_numeric(df[para_name], errors='coerce')
        media_nivel = int(df[para_name].mean().round())
        df[para_name].fillna(media_nivel, inplace=True)

    # Criar datetime auxiliar para ordenação e cálculo
    df["datetime"] = pd.to_datetime(df["Dia de Medição"] + " " + df["Hora de Medição"], dayfirst=True, errors="coerce")

    # Extrair ID da pessoa
    df["person_id"] = df["Pessoa"].astype(int)

    # Calcular tempo em horas desde a 1ª medição da pessoa
    df.sort_values(by=["person_id", "datetime"], inplace=True)
    df["Tempo"] = df.groupby("person_id")["datetime"].transform(lambda x: (x - x.min()).dt.total_seconds() / 3600)
    df["Tempo"] = df["Tempo"].round(2)
    df["Tempo"].fillna(df["Tempo"].median(), inplace=True)

    # Manter a Data de Nascimento no formato original (não transformar para datetime.date)
    # Garante que a coluna é string e tem o formato correto
    df["Data de Nascimento"] = df["Data de Nascimento"].astype(str).str.strip()

    df["Dia de Medição"] = df["Dia de Medição"].astype(str)
    df["Hora de Medição"] = df["Hora de Medição"].astype(str)
    df["Data de Nascimento"] = pd.to_datetime(df["Data de Nascimento"], format='%d/%m/%Y', errors='coerce').dt.date

    events = get_events()

    for event_id, event_name in events.items():
        df[event_name].fillna(0, inplace=True)

    # Manter apenas a última medição por pessoa
    if not importBD:
        df = df.groupby("person_id", as_index=False).last()



    # Guardar novo CSV com a coluna "Tempo"
    df.to_csv("detectid_com_tempo.csv", index=False)



    return df