import pandas as pd
from lifelines import KaplanMeierFitter
from lifelines import KaplanMeierFitter
from io import BytesIO
import matplotlib.pyplot as plt
from django.http import HttpResponse
import pandas as pd
from .models import Measurement, PersonExt

def grafico_individual(person_id):
    """
    @brief Gera gráfico de sobrevivência por grupos de TA Sistólica com destaque para o utente.
    @param person_id ID do utente.
    @return HttpResponse com imagem PNG.
    """
    # CSV com os dados para construir o gráfico
    df = pd.read_csv("./detectid.csv", encoding='utf-8')
    person_firstname = PersonExt.objects.get(person_id=person_id).first_name
    person_lastname = PersonExt.objects.get(person_id=person_id).last_name
    # Limpeza
    df["Tempo"].fillna(df["Tempo"].median(), inplace=True)
    df["DESCOMPENSAÇÃO"].fillna(0, inplace=True)
    df = df.dropna(subset=["Tempo", "DESCOMPENSAÇÃO", "TA Sistólica"])

    # Limiares
    limiar = 100.5
    limiar2 = 119.5
    limiar3 = 134.5
    param = "TA Sistólica"
    evento = "DESCOMPENSAÇÃO"

    # Criar grupos
    df['grupo_' + param] = df[param].apply(lambda x:
        'Baixo' if x < limiar else
        'Normal Baixo' if limiar <= x < limiar2 else
        'Normal Alto' if limiar2 <= x < limiar3 else
        'Alto'
    )

    # Medição do utente via ORM
    medicao = (
        Measurement.objects
        .filter(person_id=person_id, measurement_concept_id=4)
        .order_by('-measurement_datetime')
        .first()
    )

    if not medicao:
        return HttpResponse("Medição de TA Sistólica não encontrada para este utente", status=404)

    valor_ta = medicao.value_as_number

    # Determinar o grupo do utente
    if valor_ta < limiar:
        grupo_ut = 'Baixo'
    elif valor_ta < limiar2:
        grupo_ut = 'Normal Baixo'
    elif valor_ta < limiar3:
        grupo_ut = 'Normal Alto'
    else:
        grupo_ut = 'Alto'

    # Criar gráfico
    fig, ax = plt.subplots(figsize=(7, 5))
    ax.axhspan(0.6, 1, color='green', alpha=0.2, label="Área Segura (Verde)")
    ax.axhspan(0.4, 0.6, color='yellow', alpha=0.2, label="Área de Atenção (Amarelo)")
    ax.axhspan(0, 0.4, color='red', alpha=0.2, label="Área Crítica (Vermelho)")

    cores = {
        'Baixo': 'blue',
        'Normal Baixo': 'orange',
        'Normal Alto': 'green',
        'Alto': 'red'
    }

    tempo_marcado = 500
    grupos = df.groupby('grupo_' + param)

    for grupo_nome, dados in grupos:
        kmf = KaplanMeierFitter()
        kmf.fit(dados['Tempo'], event_observed=dados[evento], label=grupo_nome)
        kmf.plot_survival_function(ax=ax, ci_show=False, color=cores.get(grupo_nome, 'black'))

        if grupo_nome == grupo_ut:
            prob = kmf.predict(tempo_marcado)
            ax.scatter(tempo_marcado, prob, color=cores[grupo_nome], s=100, zorder=3, label=f"Utente (TA={valor_ta})")
            ax.annotate(f"{prob:.2f}", (tempo_marcado, prob), textcoords="offset points", xytext=(-10,-10), ha='center', color=cores[grupo_nome])

    plt.rcParams.update({'font.size': 12, 'font.family': 'DejaVu Sans'})
    plt.title(f"Grupo de {param} - {person_firstname} {person_lastname}", fontsize=16, weight='bold')
    ax.set_xlabel("Tempo", fontsize=12)
    ax.set_ylabel(f"Probabilidade de não ocorrer {evento}", fontsize=12)
    ax.grid(True, linestyle='--', alpha=0.5)
    ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.15), ncol=3, fontsize=10, frameon=False)

    # Imagem final
    buffer = BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    return HttpResponse(buffer.getvalue(), content_type='image/png')
















def grafico():
    #Ler Dados
    df = pd.read_excel("./Orange/detect.id.xlsx")
    #Preencher dados
    df_clean = df.dropna(subset=["Tempo", "DESCOMPENSAÇÃO"])
    df["Tempo"].fillna(df["Tempo"].median(), inplace=True)
    df["DESCOMPENSAÇÃO"].fillna(0, inplace=True) 

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

    limiar = 100.5
    limiar2 = 119.5
    limiar3 =134.5
    # Escolha de evento
    eventos = ['DESCOMPENSAÇÃO','Ativação Médico', 'Aumento da Vigilância', 'Via Área Ameaçada']
    evento = eventos[0]

    # Escolha de Parametros
    params = ['NIVEL DE CONSCIÊNCIA', 'FREQUÊNCIA CARDIACA','TA Sistólica','TA Diastólica','TEMPERATURA','SpO2','NECESSIDADE DE O2','DOR']
    param = params[2]


    # Criação de um novo grupo e aplicar o limiar dividndo em dois grupos
    df['grupo_' + param] = df[param].apply(lambda x: 
        'Baixo' if x < limiar else 
        'Normal Baixo' if limiar <= x < limiar2 else 
        'Normal Alto' if limiar2 <= x < limiar3 else 
        'Alto'
    )


    grupo_alto = df[df['grupo_' + param] == 'Alto']
    grupo_normalAlto = df[df['grupo_' + param] == 'Normal Alto']
    grupo_normalBaixo = df[df['grupo_' + param] == 'Normal Baixo']
    grupo_baixo = df[df['grupo_' + param] == 'Baixo']

    # Verificar a quantidade de dados em cada grupo
    print(grupo_alto.shape, grupo_baixo.shape)


    # Criar os Kaplan-Meier para cada grupo
    kmf_alto = KaplanMeierFitter()
    kmf_baixo = KaplanMeierFitter()
    kmf_normalAlto = KaplanMeierFitter()
    kmf_normalBaixo = KaplanMeierFitter()


    kmf_alto.fit(grupo_alto['Tempo'], event_observed=grupo_alto[evento], label="Alto")
    kmf_normalAlto.fit(grupo_normalAlto['Tempo'], event_observed=grupo_normalAlto[evento], label="Normal Alto")
    kmf_normalBaixo.fit(grupo_normalBaixo['Tempo'], event_observed=grupo_normalBaixo[evento], label="Normal Baixo")
    kmf_baixo.fit(grupo_baixo['Tempo'], event_observed=grupo_baixo[evento], label="Baixo")

    tempo_marcado = 500
    prob_alto = kmf_alto.predict(tempo_marcado)
    prob_normalAlto = kmf_normalAlto.predict(tempo_marcado)
    prob_normalBaixo = kmf_normalBaixo.predict(tempo_marcado)
    prob_baixo = kmf_baixo.predict(tempo_marcado)

    prob_alto_alerta = kmf_alto.predict(tempo_marcado + 24)
    prob_normalAlto_alerta = kmf_normalAlto.predict(tempo_marcado + 24)
    prob_normalBaixo_alerta = kmf_normalBaixo.predict(tempo_marcado + 24)
    prob_baixo_alerta = kmf_baixo.predict(tempo_marcado + 24)



    fig, ax = plt.subplots()

    # Adicionar áreas coloridas
    ax.axhspan(0.6, 1, color='green', alpha=0.2, label="Área Segura (Verde)")
    ax.axhspan(0.4, 0.6, color='yellow', alpha=0.2, label="Área de Atenção (Amarelo)")
    ax.axhspan(0, 0.4, color='red', alpha=0.2, label="Área Crítica (Vermelho)")

    # Plot das curvas
    kmf_alto.plot_survival_function(ax=ax, ci_show=False)
    kmf_normalAlto.plot_survival_function(ax=ax, ci_show=False)
    kmf_normalBaixo.plot_survival_function(ax=ax, ci_show=False)
    kmf_baixo.plot_survival_function(ax=ax, ci_show=False)

    # Alertas
    if(prob_alto > 0.6 and prob_alto_alerta < 0.6):
        print("ALERTA Amarelo!!!!! Ponto vermelho")

    if(prob_alto > 0.4 and prob_alto_alerta < 0.4):
        print("ALERTA Vermelho!!!!! Ponto vermelho")

    if(prob_baixo > 0.6 and prob_baixo_alerta < 0.6):
        print("ALERTA Amarelo!!!!! Ponto azul")

    if(prob_baixo > 0.4 and prob_baixo_alerta < 0.4):
        print("ALERTA Vermelho!!!!! Ponto azul")

    if(prob_normalAlto > 0.6 and prob_normalAlto_alerta < 0.6):
        print("ALERTA Amarelo!!!!! Ponto verde")

    if(prob_normalAlto > 0.4 and prob_normalAlto_alerta < 0.4):
        print("ALERTA Vermelho!!!!! Ponto verde")

    if(prob_normalBaixo > 0.6 and prob_normalBaixo_alerta < 0.6):
        print("ALERTA Amarelo!!!!! Ponto amarelo")

    if(prob_normalBaixo > 0.4 and prob_normalBaixo_alerta < 0.4):
        print("ALERTA Vermelho!!!!! Ponto amarelo")    

    # Adicionar o ponto marcado para cada grupo
    plt.scatter(tempo_marcado, prob_alto, color='red', label="Alto - Ponto", zorder=3)
    plt.scatter(tempo_marcado, prob_baixo, color='blue', label="Baixo - Ponto", zorder=3)
    plt.scatter(tempo_marcado, prob_normalAlto, color='green', label="Normal Alto - Ponto", zorder=3)
    plt.scatter(tempo_marcado, prob_normalBaixo, color='orange', label="Normal Baixo - Ponto", zorder=3)

    # Ver os valores
    plt.annotate(f"{prob_alto:.2f}", (tempo_marcado, prob_alto), textcoords="offset points", xytext=(-10,-10), ha='center', color='red')
    plt.annotate(f"{prob_baixo:.2f}", (tempo_marcado, prob_baixo), textcoords="offset points", xytext=(-10,10), ha='center', color='blue')
    plt.annotate(f"{prob_normalAlto:.2f}", (tempo_marcado, prob_normalAlto), textcoords="offset points", xytext=(-10,-10), ha='center', color='green')
    plt.annotate(f"{prob_normalBaixo:.2f}", (tempo_marcado, prob_normalBaixo), textcoords="offset points", xytext=(-10,10), ha='center', color='orange')

    plt.title("Grupo " + param + " / Evento " + evento)
    plt.xlabel("Tempo")
    plt.ylabel("Probabilidade de Sobrevivência")
    plt.legend()
    plt.grid()

