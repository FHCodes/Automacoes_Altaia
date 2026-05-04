import os
from jira import JIRA
from datetime import datetime

# --- Configurações de Acesso ---
JIRA_SERVER = 'https://alabs.atlassian.net'
JIRA_EMAIL = 'felipe-s-henriques@openlabs.com.br'
API_TOKEN = 'ATATT3xFfGF0E4Whh0N8BG4GAEEa2ot7dvFitdx_15-7UF0ijKXexUgRNUuxX0a3PS02K-G9oPNgSHtus6nHu8spgf2dPtxEVHGdqfQ8OiHm6TCTkZdoA7tEw74WQcZAAK6vLgiL4whG-s3FZTCfCnPRgbckmhdgcurjuD-2Kgbdb5KJrmP1Dwo=42264AD5'

# Conexão
jira = JIRA(server=JIRA_SERVER, basic_auth=(JIRA_EMAIL, API_TOKEN))

def lancar_horas_txt_puro(caminho_arquivo):
    if not os.path.exists(caminho_arquivo):
        print(f"❌ Arquivo {caminho_arquivo} não encontrado.")
        return

    print(f"🚀 Lendo arquivo TXT: {caminho_arquivo}")

    with open(caminho_arquivo, 'r', encoding='utf-8-sig') as file:
        # Pula a primeira linha (cabeçalho)
        linhas = file.readlines()[1:]

        for num_linha, conteudo in enumerate(linhas, start=2):
            # Remove quebras de linha e separa por '|'
            partes = conteudo.split('|')

            # Limpeza absoluta de espaços em cada campo
            issue_key = partes[0].strip()
            tempo_gasto = partes[1].strip()
            comentario = partes[2].strip()
            data_str = partes[3].strip()

            try:
                
                # 1. Converte a data
                base_date = datetime.strptime(data_str, '%d/%m/%Y')
                
                # SOLUÇÃO DO FUSO HORÁRIO:
                # Adicionamos 12 horas para que o Jira não jogue o lançamento para o dia anterior
                data_obj = base_date.replace(hour=12, minute=0)


            except Exception as e:
                print(f"❌ Erro na linha {num_linha} ({issue_key}): {e}")


            # 3. Define comentário padrão se estiver vazio
            txt_comentario = comentario if comentario else " "

            try:
                # Executa o lançamento oficial
                jira.add_worklog(
                    issue=issue_key,
                    timeSpent=tempo_gasto,
                    comment=txt_comentario,
                    started=data_obj
                )
                print(f"✅ Sucesso na linha {num_linha} - Lançando {tempo_gasto} na issue {issue_key} (Data: {data_str})...")
            
            except Exception as e:
                print(f"❌ Erro na linha {num_linha} ({issue_key}): {e}")
            
# Execução
lancar_horas_txt_puro('horas.txt')