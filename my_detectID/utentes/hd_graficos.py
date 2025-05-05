import pandas as pd
from lifelines import KaplanMeierFitter
from lifelines import KaplanMeierFitter
from io import BytesIO
import matplotlib.pyplot as plt
from django.http import HttpResponse
import pandas as pd
from .models import Measurement, PersonExt, VisitOccurrence

    # TABELA DE LIMIARES PARA CADA PARAMETRO #
    # Nivel de Consciencia 	- < 13.5	- Baixo
    # 			    	    - 13.5 - 14.5	- Intermédio
    # 			            - >= 14.5	- Normal

    # Frequencia Cardiaca	- < 69.5	- Baixo
    # 			            - 69.5 - 84.5	- Normal Baixo
    # 			            - 84.5 - 100.5	- Normal Alto
    # 			            - >= 100.5	- Alto

    # TA Sistólica	    	- < 100.5	- Baixo
    # 			            - 100.5 - 119.5	- Normal Baixo
    # 			            - 119.5 - 134.5	- Normal Alto
    # 			            - >= 134.5	- Alto

    # TA Diastólica		    - < 55.5	- Baixo
    # 		        	    - 55.5 - 65.5	- Normal Baixo
    # 		        	    - 65.5 - 76.5	- Normal Alto
    # 		        	    - >= 76.5	- Alto

    # Temperatura		    - < 36.05	- Baixo
    # 		        	    - 36.05 - 36.55	- Normal Baixo
    # 		        	    - 36.55 - 37.05	- Normal
    # 		        	    - >= 37.05	- Alto

    # SpO2			        - < 90.5	- Muito Baixo
    # 		        	    - 90.5 - 93.5	- Baixo
    # 		        	    - 93.5 - 95.5	- Normal Baixo
    # 		        	    - >= 95.5	- Normal
    
def grafico_individual(person_id, param_id, evento_id):
    """
    @brief Gera gráfico de sobrevivência para qualquer parâmetro clínico com destaque para o utente.
    @param person_id ID do utente.
    @param param_id ID do parâmetro (1 a 8).
    @param evento_id ID do evento (1 a 4).
    @return HttpResponse com imagem PNG.
    """

    # Mapas
    parametros = {
        "1": ("SpO2", [90, 95, 98]),
        "2": ("NECESSIDADE DE O2", [1, 2, 3]),
        "3": ("FREQUÊNCIA CARDIACA", [60, 100, 120]),
        "4": ("TA Sistólica", [100.5, 119.5, 134.5]),
        "5": ("TA Diastólica", [60, 80, 90]),
        "6": ("TEMPERATURA", [35.5, 37.5, 38.5]),
        "7": ("NIVEL DE CONSCIÊNCIA", [8, 13, 15]),
        "8": ("DOR", [1, 2, 3]),
    }

    eventos = {
        "1": "DESCOMPENSAÇÃO",
        "2": "Ativação Médico",
        "3": "Aumento da Vigilância",
        "4": "Via Área Ameaçada"
    }

    if str(param_id) not in parametros:
        return HttpResponse("Parâmetro inválido", status=400)

    if str(evento_id) not in eventos:
        return HttpResponse("Evento inválido", status=400)

    nome_param, (limiar1, limiar2, limiar3) = parametros[str(param_id)]
    evento_nome = eventos[str(evento_id)]
    
    # Dados
    df = pd.read_csv("./detectid.csv", encoding='utf-8')
    df["Tempo"].fillna(df["Tempo"].median(), inplace=True)
    df[evento_nome].fillna(0, inplace=True)
    df[nome_param] = pd.to_numeric(df[nome_param], errors='coerce')
    df = df.dropna(subset=["Tempo", evento_nome, nome_param])

    # Grupos
    df['grupo_' + nome_param] = df[nome_param].apply(
        lambda x:
        'Baixo' if x < limiar1 else
        'Normal Baixo' if x < limiar2 else
        'Normal Alto' if x < limiar3 else
        'Alto'
    )

    # Medição do utente
    medicao = (
        Measurement.objects
        .filter(person_id=person_id, measurement_concept_id=param_id)
        .order_by('-measurement_datetime')
        .first()
    )

    if not medicao:
        return HttpResponse(f"Medição de {nome_param} não encontrada para este utente", status=404)

    valor = medicao.value_as_number

    if valor < limiar1:
        grupo_ut = 'Baixo'
    elif valor < limiar2:
        grupo_ut = 'Normal Baixo'
    elif valor < limiar3:
        grupo_ut = 'Normal Alto'
    else:
        grupo_ut = 'Alto'

    # Tempo relativo do utente (em horas)
    visita = VisitOccurrence.objects.filter(person_id=person_id).order_by('-visit_start_datetime').first()
    if not visita:
        return HttpResponse("Visita não encontrada", status=404)

    tempo_utente = (medicao.measurement_datetime - visita.visit_start_datetime).total_seconds() / 3600

    # Gráfico
    person = PersonExt.objects.get(person_id=person_id)
    fig, ax = plt.subplots(figsize=(7, 5))
    ax.axhspan(0.6, 1, color='green', alpha=0.2)
    ax.axhspan(0.4, 0.6, color='yellow', alpha=0.2)
    ax.axhspan(0, 0.4, color='red', alpha=0.2)

    cores = {
        'Baixo': 'blue',
        'Normal Baixo': 'orange',
        'Normal Alto': 'green',
        'Alto': 'red'
    }

    grupos = df.groupby('grupo_' + nome_param)

    for grupo_nome, dados in grupos:
        kmf = KaplanMeierFitter()
        kmf.fit(dados['Tempo'], event_observed=dados[evento_nome], label=grupo_nome)
        kmf.plot_survival_function(ax=ax, ci_show=False, color=cores.get(grupo_nome, 'black'))

        if grupo_nome == grupo_ut:
            prob = kmf.predict(tempo_utente)
            ax.scatter(tempo_utente, prob, color=cores[grupo_nome], s=100, zorder=3, label=f"Utente ({valor})")
            ax.annotate(f"{prob:.2f}", (tempo_utente, prob), textcoords="offset points", xytext=(-10, -10), ha='center')

    plt.title(f"Grupos de {nome_param} - {person.first_name} {person.last_name}", fontsize=14)
    ax.set_xlabel("Tempo desde entrada (horas)")
    ax.set_ylabel(f"Probabilidade de não ocorrer {evento_nome}")
    ax.grid(True, linestyle='--', alpha=0.5)
    ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.15), ncol=3, fontsize=10, frameon=False)

    buffer = BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    return HttpResponse(buffer.getvalue(), content_type='image/png')



