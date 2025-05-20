import pandas as pd
from lifelines import KaplanMeierFitter

_csv_data = None

MODELOS_KM = {}

LIMIARES = {}

def get_param_group(param, value):
    global LIMIARES
    if pd.isna(value):
        return None
    
    for x in LIMIARES:
        nome_param, (limiar1, limiar2, limiar3) = LIMIARES[x]
        if nome_param == param:
            if value < limiar1:
                return 'baixo'
            elif value < limiar2:
                return 'normal baixo'
            elif value < limiar3:
                return 'normal alto'
            else:
                return 'alto'
    return None


def trainKM():
    global _csv_data, MODELOS_KM,LIMIARES

    if _csv_data is None:
        print("A Carregar o ficheiro CSV...")

        _csv_data = getCSV()

        LIMIARES = {
        1: ("SpO2", [90, 95, 98]),
        2: ("Necessidade de O2", [1, 2, 3]),
        3: ("Frequência Cardíaca", [60, 100, 120]),
        4: ("TA Sistólica", [100.5, 119.5, 134.5]),
        5: ("TA Diastólica", [60, 80, 90]),
        6: ("Temperatura", [35.5, 37.5, 38.5]),
        7: ("Nível de Consciência", [8, 13, 15]),
        8: ("Dor", [1, 2, 3]),
        }   

        # Criar modelos KM para cada parâmetro e evento
        eventos = [
            "Descompensação",
            "Ativação Médico",
            "Aumento da Vigilância",
            "Via Área Ameaçada"
        ]
        parametros_clinicos = [
            "SpO2", "Necessidade de O2", "Frequência Cardíaca",
            "TA Sistólica", "TA Diastólica", "Temperatura",
            "Nível de Consciência", "Dor"
        ]

        #Treinar os Modelos KM
        for parametro in parametros_clinicos:
            MODELOS_KM[parametro] = {}
            for evento_col in eventos:
                MODELOS_KM[parametro][evento_col] = {}
                for grupo in ['baixo', 'normal baixo', 'normal alto', 'alto']:
                    # Filtrar os dados para este grupo
                    grupo_df = _csv_data[_csv_data[parametro].apply(lambda x: get_param_group(parametro, x)) == grupo]
                    if not grupo_df.empty:
                        kmf = KaplanMeierFitter()
                        kmf.fit(grupo_df["Tempo"], event_observed=grupo_df[evento_col], label=f"{parametro}_{grupo}")
                        MODELOS_KM[parametro][evento_col][grupo] = kmf

        kmf = KaplanMeierFitter()
        kmf.fit(_csv_data["Tempo"], _csv_data["Evento"])
        MODELOS_KM["global"] = kmf

    return _csv_data

def getLimiares():
    global LIMIARES
    return LIMIARES

def get_kaplan_model(parametro, valor, evento_id=1):
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
        "Via Área Ameaçada"
    ]
    evento = eventos[evento_id - 1]

    nome_param, (limiar1, limiar2, limiar3) = LIMIARES[parametro]

    if valor < limiar1:
        grupo = 'baixo'
    elif valor < limiar2:
        grupo = 'normal baixo'
    elif valor < limiar3:
        grupo = 'normal alto'
    else:
        grupo = 'alto'


    return MODELOS_KM.get(nome_param, {}).get(evento, {}).get(grupo, None)

def get_global_kaplan_model():
    return MODELOS_KM.get("global")

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


    # Guardar novo CSV com a coluna "Tempo"
    df.to_csv("detectid_com_tempo.csv", index=False)



    return df
