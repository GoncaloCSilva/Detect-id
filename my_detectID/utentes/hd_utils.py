import os
import numpy as np
import pandas as pd
from lifelines import KaplanMeierFitter
from sklearn.model_selection import train_test_split
from sksurv.ensemble import RandomSurvivalForest
from sksurv.util import Surv
from sklearn.preprocessing import StandardScaler
import pickle


_csv_data = None

MODELOS_KM = {}

MODELOS_RSF = {}

LIMIARES = {}

CURRENT_MODEL = 1 # 1-> KM 2-> RSF

def get_param_group(param, value):
    global LIMIARES
    if pd.isna(value):
        return None
    
    for x in LIMIARES:
        nome_param, (limiar1, limiar2) = LIMIARES[x]
        if nome_param == param:
            if value < limiar1:
                return 'baixo'
            elif value < limiar2:
                return 'normal'
            else:
                return 'alto'
    return None

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
    global _csv_data, MODELOS_KM,MODELOS_RSF,LIMIARES

    if os.path.exists("./pickle/rsf_modelos.pkl") and os.path.exists("./pickle/km_modelos.pkl"):
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

        # Criar modelos KM para cada parâmetro e evento
        eventos = [
            "Descompensação",
            "Ativação Médico",
            "Aumento da Vigilância",
            "Via Área Ameaçada",
            "Suporte Ventilatório",
            "Suporte Circulatório",
            "Mortalidade"
        ]
        parametros_clinicos = [
            "SpO2", "Necessidade de O2", "Frequência Cardíaca",
            "TA Sistólica", "TA Diastólica", "Temperatura",
            "Nível de Consciência", "Dor"
        ]

        #Treinar os Modelos KM
        for parametro in parametros_clinicos:
            MODELOS_KM[parametro] = {}
            MODELOS_RSF[parametro] = {}
            for evento_col in eventos:
                MODELOS_KM[parametro][evento_col] = {}
                MODELOS_RSF[parametro][evento_col] = {}
                for grupo in ['baixo', 'normal', 'alto']:
                    # Filtrar os dados para este grupo
                    grupo_df = _csv_data[_csv_data[parametro].apply(lambda x: get_param_group(parametro, x)) == grupo]
                    if not grupo_df.empty:

                        #### KaplanMeier ####
                        
                        kmf = KaplanMeierFitter()
                        kmf.fit(grupo_df["Tempo"], event_observed=grupo_df[evento_col], label=f"{parametro}_{grupo}")
                        MODELOS_KM[parametro][evento_col][grupo] = kmf

                        #### Random Surival Forest ####
                        X = _csv_data[[parametro]]
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

                        MODELOS_RSF[parametro][evento_col][grupo] = rsf

        kmf = KaplanMeierFitter()
        kmf.fit(_csv_data["Tempo"], _csv_data["Evento"])
        MODELOS_KM["global"] = kmf


        X = _csv_data[parametros_clinicos]
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

def get_model(parametro, valor, evento_id=1):
    """
    @brief: Devolve o modelo Kaplan-Meier treinado para o parâmetro e grupo fornecido.
    @param parametro: ID do parâmetro clínico (ex: 1 -> 'SpO2')
    @param valor: Valor da medicao do parametro
    @return: Objeto KaplanMeierFitter treinado ou None
    """

    eventos = [
        "Descompensação",
        "Ativação Médico",
        "Aumento da Vigilância",
        "Via Área Ameaçada",
        "Suporte Ventilatório",
        "Suporte Circulatório",
        "Mortalidade"
    ]
    evento = eventos[evento_id - 1]

    nome_param, (limiar1, limiar2) = LIMIARES[parametro]

    if parametro == 8:
        grupo='normal'
    else:
        if valor < limiar1:
            grupo = 'baixo'
        elif valor < limiar2:
            grupo = 'normal'
        else:
            grupo = 'alto'
    
    
    if CURRENT_MODEL == 1:
        return MODELOS_KM.get(nome_param, {}).get(evento, {}).get(grupo, None)
    else:
        return MODELOS_RSF.get(nome_param, {}).get(evento, {}).get(grupo, None)

def get_global_model():
    if CURRENT_MODEL == 1:
        return MODELOS_KM.get("global") 
    else:
        return MODELOS_RSF.get("global")


def getCSV(file_path = "detectid.csv"):

    df = pd.read_csv(file_path)

    # Processamento dos tipos
    numeric_cols = df.select_dtypes(include='number').columns
    df[numeric_cols] = df[numeric_cols].fillna(df[numeric_cols].mean())

    # NIVEL DE CONSCIÊNCIA como inteiro com média preenchida

    parametros_clinicos = [
    "SpO2", "Necessidade de O2", "Frequência Cardíaca",
    "TA Sistólica", "TA Diastólica", "Temperatura",
    "Nível de Consciência", "Dor"
    ]

    for param in parametros_clinicos:
        df[param] = pd.to_numeric(df[param], errors='coerce')
        media_nivel = int(df[param].mean().round())
        df[param].fillna(media_nivel, inplace=True)

    # Criar datetime auxiliar para ordenação e cálculo
    df["datetime"] = pd.to_datetime(df["Dia de Medição"] + " " + df["Hora de Medição"], dayfirst=True, errors="coerce")

    # Extrair ID da pessoa
    df["person_id"] = df["Pessoa"].str.extract(r"(\d+)").astype(int)

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

    df["Descompensação"].fillna(df["Descompensação"].median(), inplace=True)
    df["Ativação Médico"].fillna(df["Ativação Médico"].median(), inplace=True)
    df["Aumento da Vigilância"].fillna(df["Aumento da Vigilância"].median(), inplace=True)
    df["Via Área Ameaçada"].fillna(df["Via Área Ameaçada"].median(), inplace=True)
    df["Suporte Ventilatório"].fillna(df["Suporte Ventilatório"].median(), inplace=True)
    df["Suporte Circulatório"].fillna(df["Suporte Circulatório"].median(), inplace=True)
    df["Mortalidade"].fillna(0, inplace=True)

    # Manter apenas a última medição por pessoa
    df = df.groupby("person_id", as_index=False).last()



    # Guardar novo CSV com a coluna "Tempo"
    df.to_csv("detectid_com_tempo.csv", index=False)



    return df
