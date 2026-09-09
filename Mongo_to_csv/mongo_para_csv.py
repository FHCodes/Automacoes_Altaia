import pandas as pd
from pymongo import MongoClient

# ==========================================
# 1. CONFIGURAÇÕES DO AMBIENTE DEV
# ==========================================
# Substitua pela URI do seu MongoDB de desenvolvimento
MONGO_URI = "mongodb://usuario:senha@localhost:27017/" 
DATABASE_NAME = "nome_do_seu_banco"
COLLECTION_NAME = "nome_da_sua_colecao"

# ==========================================
# 2. DEFINIÇÃO DA QUERY
# ==========================================
# Coloque aqui a sua query. 
# Exemplo: Buscar todos os usuários ativos
query = {
    "status": "ativo"
}

# (Opcional) Projeção: Use se quiser definir quais campos trazer ou esconder
# Exemplo: Omitir o _id e trazer apenas nome e email
# projection = {"_id": 0, "nome": 1, "email": 1}


def exportar_mongo_para_csv(uri, db_name, collection_name, query, arquivo_saida):
    try:
        # Conectando ao cluster do MongoDB
        print("🔌 Conectando ao MongoDB...")
        client = MongoClient(uri)
        db = client[db_name]
        collection = db[collection_name]

        # Executando a busca
        print("🔍 Executando a query...")
        # Se for usar projection, altere para: collection.find(query, projection)
        cursor = collection.find(query) 
        
        # Convertendo o resultado em uma lista de dicionários
        dados = list(cursor)

        if len(dados) == 0:
            print("⚠️ A query não retornou nenhum documento.")
            return

        # Transformando a lista em um DataFrame do Pandas
        print(f"📊 Processando {len(dados)} documentos...")
        df = pd.DataFrame(dados)

        # Como o MongoDB retorna o '_id' como um objeto BSON (ObjectId), 
        # convertê-lo para string evita problemas na hora de abrir o CSV.
        if '_id' in df.columns:
            df['_id'] = df['_id'].astype(str)

        # Exportando para CSV
        # index=False impede que o Pandas crie uma coluna extra de numeração
        df.to_csv(arquivo_saida, index=False, encoding='utf-8')
        print(f"✅ Sucesso! Dados exportados para: {arquivo_saida}")

    except Exception as e:
        print(f"❌ Ocorreu um erro: {e}")
        
    finally:
        # Boas práticas: sempre feche a conexão!
        if 'client' in locals():
            client.close()

if __name__ == "__main__":
    NOME_DO_ARQUIVO = "resultado_query_dev.csv"
    exportar_mongo_para_csv(MONGO_URI, DATABASE_NAME, COLLECTION_NAME, query, NOME_DO_ARQUIVO)