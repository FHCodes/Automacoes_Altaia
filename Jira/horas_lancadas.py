from jira import JIRA
from datetime import datetime

# Configurações de acesso
JIRA_SERVER = 'https://alabs.atlassian.net'
EMAIL = 'felipe-s-henriques@openlabs.com.br'
API_TOKEN = 'ATATT3xFfGF0E4Whh0N8BG4GAEEa2ot7dvFitdx_15-7UF0ijKXexUgRNUuxX0a3PS02K-G9oPNgSHtus6nHu8spgf2dPtxEVHGdqfQ8OiHm6TCTkZdoA7tEw74WQcZAAK6vLgiL4whG-s3FZTCfCnPRgbckmhdgcurjuD-2Kgbdb5KJrmP1Dwo=42264AD5'

# Filtros do relatório
PROJETO = 'ALTAIAVIVO'
DATA_INICIO = datetime(2026, 4, 27)
DATA_FIM = datetime(2026, 4, 30)

jira = JIRA(server=JIRA_SERVER, basic_auth=(EMAIL, API_TOKEN))

def buscar_meus_lancamentos():
    print(f"Buscando lançamentos de {EMAIL} no projeto {PROJETO}...")
    
    # JQL específica para evitar o erro de "consulta ilimitada" [cite: 25, 41]
    # Filtra apenas issues do projeto onde você lançou horas no período
    jql = f'project = "{PROJETO}" AND worklogAuthor = currentUser() AND worklogDate >= "{DATA_INICIO.strftime("%Y-%m-%d")}"'
    
    issues = jira.search_issues(jql, maxResults=100)
    relatorio = {}

    for issue in issues:
        # Busca TODOS os worklogs da tarefa para não cair no limite de 20 da API [cite: 60, 63]
        worklogs = jira.worklogs(issue.key)
        
        for wl in worklogs:
            # Filtra pelo seu e-mail e pelo intervalo de datas [cite: 55, 92]
            wl_date = datetime.strptime(wl.started.split('T')[0], '%Y-%m-%d')
            
            if wl.author.emailAddress == EMAIL and DATA_INICIO <= wl_date <= DATA_FIM:
                data_str = wl_date.strftime('%d/%m/%Y')
                horas = wl.timeSpentSeconds / 3600 # Converte segundos para horas 
                
                if data_str not in relatorio:
                    relatorio[data_str] = []
                
                relatorio[data_str].append({
                    'issue': issue.key,
                    'horas': horas,
                    'comentario': getattr(wl, 'comment', 'Sem descrição')
                })

    # Exibição dos dados organizados [cite: 95]
    print(f"\n--- Extrato de Horas: {PROJETO} ---")
    total_geral = 0
    # Lista de referência (deve estar antes do loop)
    DIAS_DA_SEMANA = ["segunda-feira", "terça-feira", "quarta-feira", "quinta-feira", "sexta-feira", "sábado", "domingo"]

    # O seu bloco ajustado:
    for dia in sorted(relatorio.keys(), key=lambda x: datetime.strptime(x, '%d/%m/%Y')):
        # 1. Transformamos o texto 'dia' em um objeto de data para liberar as funções
        data_obj = datetime.strptime(dia, '%d/%m/%Y') 
        
        # 2. Usamos a função .weekday() para descobrir o dia (0 a 6) e pegar o nome na lista
        nome_dia = DIAS_DA_SEMANA[data_obj.weekday()] 
        
        print(f"\n📅 Dia: {dia} - {nome_dia}")
        total_dia = 0
        for item in relatorio[dia]:
            print(f"  - [{item['issue']}] {item['horas']:.2f}h | {item['comentario']}")
            total_dia += item['horas']
        print(f"  Total do dia: {total_dia:.2f}h")
        total_geral += total_dia

    print(f"\n{'='*30}")
    print(f"TOTAL ACUMULADO NO PERÍODO: {total_geral:.2f}h")

if __name__ == "__main__":
    buscar_meus_lancamentos()