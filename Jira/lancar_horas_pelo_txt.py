import os
from jira import JIRA
from datetime import datetime
import csv

# --- Configurações de Acesso ---
JIRA_SERVER = 'https://alabs.atlassian.net'
# JIRA_EMAIL = 'felipe-s-henriques@openlabs.com.br'
# API_TOKEN = 'ATATT3xFfGF0E4Whh0N8BG4GAEEa2ot7dvFitdx_15-7UF0ijKXexUgRNUuxX0a3PS02K-G9oPNgSHtus6nHu8spgf2dPtxEVHGdqfQ8OiHm6TCTkZdoA7tEw74WQcZAAK6vLgiL4whG-s3FZTCfCnPRgbckmhdgcurjuD-2Kgbdb5KJrmP1Dwo=42264AD5'

# Conexão
jira = JIRA(server=JIRA_SERVER, basic_auth=(JIRA_EMAIL, API_TOKEN))

import csv
import os

def lancar_horas_por_csv(caminho_arquivo):
    if not os.path.exists(caminho_arquivo):
        print(f"❌ Arquivo {caminho_arquivo} não encontrado.")
        return

    print(f"🚀 Lendo arquivo CSV: {caminho_arquivo}")

    with open(caminho_arquivo, mode='r', encoding='latin-1') as file:
        
        # ⚠️ MUDANÇA AQUI: Trocamos o delimiter para vírgula ','
        leitor = csv.reader(file, delimiter=';') 
        
        # Pula a primeira linha (cabeçalho)
        next(leitor, None) 
        
        for linha in leitor:
            
            # PROTEÇÃO: Se a linha for vazia ou não tiver pelo menos 2 colunas, pula e não quebra o código
            if not linha:
                continue
            
            # Pega os dados direto pela posição da coluna
            issue = linha[0].strip()
            horas = linha[1].strip()
            comentario = linha[2].strip() if linha[2] else "lançamento de horas"  # Comentário é opcional
            data_str = linha[3].strip() if linha[3] else None  # Data é opcional
    
            
            # ... continuação com o bloco try/except da data e lançamento ...

            try:
                
                # 1. Converte a data
                base_date = datetime.strptime(data_str, '%d/%m/%Y')
                
                # SOLUÇÃO DO FUSO HORÁRIO:
                # Adicionamos 12 horas para que o Jira não jogue o lançamento para o dia anterior
                data_obj = base_date.replace(hour=12, minute=0)


            except Exception as e:
                print(f"❌ ({issue}): {e}")


            print(f"⏳ Issue: {issue}, Horas: {horas}, Comentário: {comentario}, Data: {data_str}...")

            try:
                # Executa o lançamento oficial
                jira.add_worklog(
                    issue=issue,
                    timeSpent=horas,
                    comment=comentario,
                    started=data_obj
                )
                print(f"✅ Lançando {horas} na issue {issue} (Data: {data_str})...")
            
            except Exception as e:
                print(f"❌ ({issue}): {e}")
            
# Execução
lancar_horas_por_csv('horas.csv')