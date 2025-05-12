import pandas as pd
from lifelines import KaplanMeierFitter

_csv_data = None
MODELOS_KM = {}
__limiares = {
        1: ("SpO2", [90, 95, 98]),
        2: ("NECESSIDADE DE O2", [1, 2, 3]),
        3: ("FREQUÊNCIA CARDIACA", [60, 100, 120]),
        4: ("TA Sistólica", [100.5, 119.5, 134.5]),
        5: ("TA Diastólica", [60, 80, 90]),
        6: ("TEMPERATURA", [35.5, 37.5, 38.5]),
        7: ("NIVEL DE CONSCIÊNCIA", [8, 13, 15]),
        8: ("DOR", [1, 2, 3]),
}

def get_csv_data():
    global _csv_data, MODELOS_KM

    if _csv_data is None:
        print("A Carregar o ficheiro CSV...")
        _csv_data = pd.read_csv("./detectid_com_tempo.csv", encoding='utf-8')

        # Limpeza e transformação dos dados
        _csv_data["Tempo"].fillna(_csv_data["Tempo"].median(), inplace=True)
        parametros_clinicos = [
            "SpO2", "NECESSIDADE DE O2", "FREQUÊNCIA CARDIACA",
            "TA Sistólica", "TA Diastólica", "TEMPERATURA",
            "NIVEL DE CONSCIÊNCIA", "DOR"
        ]

        for param in parametros_clinicos:
            _csv_data[param] = pd.to_numeric(_csv_data[param], errors='coerce')

        _csv_data["DESCOMPENSAÇÃO"].fillna(_csv_data["DESCOMPENSAÇÃO"].median(), inplace=True)
        _csv_data["Ativação Médico"].fillna(_csv_data["Ativação Médico"].median(), inplace=True)
        _csv_data["Aumento da Vigilância"].fillna(_csv_data["Aumento da Vigilância"].median(), inplace=True)
        _csv_data["Via Área Ameaçada"].fillna(_csv_data["Via Área Ameaçada"].median(), inplace=True)

        # Criar modelos Kaplan-Meier para cada parâmetro e evento
        eventos = [
            "DESCOMPENSAÇÃO",
            "Ativação Médico",
            "Aumento da Vigilância",
            "Via Área Ameaçada"
        ]

        def get_param_group(param, value):
            if pd.isna(value):
                return 'desconhecido'
            if param == "SpO2":
                if value < 90:
                    return 'baixo'
                elif value < 95:
                    return 'normal baixo'
                elif value < 98:
                    return 'normal alto'
                else:
                    return 'alto'
            elif param == "FREQUÊNCIA CARDIACA":
                if value < 60:
                    return 'baixo'
                elif value < 100:
                    return 'normal baixo'
                elif value < 120:
                    return 'normal alto'
                else:
                    return 'alto'
            elif param == "TA Sistólica":
                if value < 100.5:
                    return 'baixo'
                elif value < 119.5:
                    return 'normal baixo'
                elif value < 134.5:
                    return 'normal alto'
                else:
                    return 'alto'
            elif param == "TA Diastólica":
                if value < 60:
                    return 'baixo'
                elif value < 80:
                    return 'normal baixo'
                elif value < 90:
                    return 'normal alto'
                else:
                    return 'alto'
            elif param == "TEMPERATURA":
                if value < 35.5:
                    return 'baixo'
                elif value < 37.5:
                    return 'normal baixo'
                elif value < 38.5:
                    return 'normal alto'
                else:
                    return 'alto'
            elif param == "NIVEL DE CONSCIÊNCIA":
                if value < 8:
                    return 'baixo'
                elif value < 13:
                    return 'normal baixo'
                elif value < 15:
                    return 'normal alto'
                else:
                    return 'alto'
            elif param == "DOR":
                if value < 1:
                    return 'baixo'
                elif value < 2:
                    return 'normal baixo'
                elif value < 3:
                    return 'normal alto'
                else:
                    return 'alto'
            elif param == "NECESSIDADE DE O2":
                if value < 1:
                    return 'baixo'
                elif value < 2:
                    return 'normal baixo'
                elif value < 3:
                    return 'normal alto'
                else:
                    return 'alto'
            return 'default'

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

def get_kaplan_model(parametro, valor, evento_id=1):
    """
    @brief: Devolve o modelo Kaplan-Meier treinado para o parâmetro e grupo fornecido.
    @param parametro: ID do parâmetro clínico (ex: 1 -> 'SpO2')
    @param valor: Valor da medicao do parametro
    @return: Objeto KaplanMeierFitter treinado ou None
    """

    eventos = [
        "DESCOMPENSAÇÃO",
        "Ativação Médico",
        "Aumento da Vigilância",
        "Via Área Ameaçada"
    ]
    evento = eventos[evento_id - 1]

    nome_param, (limiar1, limiar2, limiar3) = __limiares[parametro]

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
