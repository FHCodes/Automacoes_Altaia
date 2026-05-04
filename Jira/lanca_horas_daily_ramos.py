

#PEGA AS HORAS DAS DAILYS DO RICARDO RAMOS JUNIOR E LANÇA NA MESMA ISSUE, COM O MESMO COMENTÁRIO

from jira import JIRA
from datetime import datetime
import pytz

tz = pytz.timezone("America/Sao_Paulo")

# Configurações de acesso
JIRA_SERVER = 'https://alabs.atlassian.net'
USER_EMAIL = 'felipe-s-henriques@openlabs.com.br'
# USER_EMAIL = 'ricardo-r-junior@openlabs.com.br'
API_TOKEN = 'ATATT3xFfGF0E4Whh0N8BG4GAEEa2ot7dvFitdx_15-7UF0ijKXexUgRNUuxX0a3PS02K-G9oPNgSHtus6nHu8spgf2dPtxEVHGdqfQ8OiHm6TCTkZdoA7tEw74WQcZAAK6vLgiL4whG-s3FZTCfCnPRgbckmhdgcurjuD-2Kgbdb5KJrmP1Dwo=42264AD5'

from jira import JIRA
from datetime import datetime

# Configurações
ISSUE_KEY = 'ALTAIAVIVO-1501'
DATA_INICIO = datetime(2026, 4, 2) 
DATA_FIM = datetime(2026, 4, 17)
NOME_FILTRO = "Ricardo Ramos Junior"
COMENTARIO_ALVO = "Daily"  # Filtro específico solicitado

def filtrar_por_usuario():
    try:
        jira = JIRA(server=JIRA_SERVER, basic_auth=(USER_EMAIL, API_TOKEN))
        
        print(f"Buscando lançamentos de {NOME_FILTRO} com o comentário '{COMENTARIO_ALVO}'...")
        
        worklogs = jira.worklogs(ISSUE_KEY)
        agrupado_por_dia = {}

        for wl in worklogs:
            # 1. Verifica se o autor é o Ricardo
            if wl.author.displayName == NOME_FILTRO:
                
                # 2. Verifica o comentário (Filtro solicitado)
                comentario = getattr(wl, 'comment', 'Sem descrição').strip()
                
                if  COMENTARIO_ALVO in comentario:
                    data_raw = wl.started.split('T')[0]
                    data_lancamento = datetime.strptime(data_raw, '%Y-%m-%d')
                    
                    # 3. Verifica o período
                    if DATA_INICIO <= data_lancamento <= DATA_FIM:
                        dia_str = data_lancamento.strftime('%d/%m/%Y')
                        horas = wl.timeSpentSeconds / 3600

                        if dia_str not in agrupado_por_dia:
                            agrupado_por_dia[dia_str] = []
                        
                        agrupado_por_dia[dia_str].append({
                            'horas': horas,
                            'comentario': comentario
                        })

        # Exibição dos dados filtrados
        if not agrupado_por_dia:
            print(f"Nenhum lançamento com o comentário '{COMENTARIO_ALVO}' encontrado.")
        else:
            print(f"\n--- Relatório Filtrado: {NOME_FILTRO} ---")
            total_geral_usuario = 0

            # Ordenação por data
            datas_ordenadas = sorted(agrupado_por_dia.keys(), key=lambda x: datetime.strptime(x, '%d/%m/%Y'))

            for dia in datas_ordenadas:
                total_dia = sum(item['horas'] for item in agrupado_por_dia[dia])
                total_geral_usuario += total_dia
                
                # Exibe o dia e apenas os logs que passaram no filtro do comentário
                #print(f"\n📅 Dia: {dia}") 
                for item in agrupado_por_dia[dia]:
                    print(f"🕒 Lançando {item['horas']:.2f}h no dia {dia}...")

                    # converte string → datetime
                    data_dt = datetime.strptime(dia, "%d/%m/%Y")
                    
                    # define um horário (Jira precisa de hora também)
                    data_dt = data_dt.replace(hour=11, minute=0)
                    
                    # adiciona timezone
                    data_dt = tz.localize(data_dt)

                    jira.add_worklog(
                        issue=ISSUE_KEY,
                        timeSpentSeconds=int(item['horas'] * 3600),  # 👈 MELHOR usar isso
                        comment=item['comentario'],
                        started=data_dt
                    )


            
            print(f"\n{'='*40}")
            print(f"TOTAL ACUMULADO DO FILTRO: {total_geral_usuario:.2f} horas")
            print(f"{'='*40}")

    except Exception as e:
        print(f"Erro: {e}")

if __name__ == "__main__":
    filtrar_por_usuario()