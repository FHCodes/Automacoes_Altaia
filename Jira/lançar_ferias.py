from jira import JIRA
from datetime import datetime, timedelta

# Configurações de acesso
JIRA_SERVER = 'https://alabs.atlassian.net'
USER_EMAIL = 'felipe-s-henriques@openlabs.com.br'
API_TOKEN = 'ATATT3xFfGF0E4Whh0N8BG4GAEEa2ot7dvFitdx_15-7UF0ijKXexUgRNUuxX0a3PS02K-G9oPNgSHtus6nHu8spgf2dPtxEVHGdqfQ8OiHm6TCTkZdoA7tEw74WQcZAAK6vLgiL4whG-s3FZTCfCnPRgbckmhdgcurjuD-2Kgbdb5KJrmP1Dwo=42264AD5'


ISSUE_KEY = 'RHBR-282'

# Configuração do lançamento
HORAS_POR_DIA = '8h'  # Formato do Jira: '8h', '1h 30m', etc.
COMENTARIO = 'ferias'

# Período
DATA_INICIO = datetime(2026, 3, 2)
DATA_FIM = datetime(2026, 3, 19)

def lancar_horas_em_massa():
    try:
        jira = JIRA(server=JIRA_SERVER, basic_auth=(USER_EMAIL, API_TOKEN))
        print(f"🚀 Iniciando lançamentos para a issue {ISSUE_KEY}...")

        data_atual = DATA_INICIO
        while data_atual <= DATA_FIM:
            # weekday() 5 = Sábado, 6 = Domingo
            if data_atual.weekday() < 5:
                # O Jira espera a data no início do dia ou em um horário específico
                # Formatamos para o padrão que a API aceita com o horário fixo (ex: 09:00)
                data_formatada = data_atual.replace(hour=11, minute=0)

                print(f"🕒 Lançando {HORAS_POR_DIA} no dia {data_atual.strftime('%d/%m/%Y')}...")
                
                # Comando que efetivamente cria o registro no Jira
                jira.add_worklog(
                    issue=ISSUE_KEY,
                    timeSpent=HORAS_POR_DIA,
                    comment=COMENTARIO,
                    started=data_formatada
                )
            else:
                print(f"⏭️ Pulando {data_atual.strftime('%d/%m/%Y')} (Fim de semana)")

            # Incrementa um dia
            data_atual += timedelta(days=1)

        print("\n✅ Todos os lançamentos foram concluídos com sucesso!")

    except Exception as e:
        print(f"❌ Erro durante o processo: {e}")

if __name__ == "__main__":
    # DICA: Sempre teste com um intervalo pequeno (1 ou 2 dias) antes de rodar o período todo
    confirmacao = input(f"Confirma o lançamento de {HORAS_POR_DIA} por dia de {DATA_INICIO.date()} até {DATA_FIM.date()}? (s/n): ")
    if confirmacao.lower() == 's':
        lancar_horas_em_massa()
    else:
        print("Operação cancelada.")