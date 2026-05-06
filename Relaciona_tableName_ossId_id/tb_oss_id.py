from lxml import etree

def mapear_catalogos(arquivo_xml, lista_busca):
    # Passo 1: Inicializar as variáveis para guardar os dados
    tablenames_encontrados = set()
    oss_ids_encontrados = set()
    ids_encontrados = set()

    # Passo 2: Fazer a leitura (parsing) do arquivo XML
    try:
        tree = etree.parse(arquivo_xml)
        root = tree.getroot()
    except Exception as e:
        print(f"Erro ao ler o arquivo XML: {e}")
        return None

    # Passo 3: Iterar diretamente nas tags 'table', ignorando o resto do arquivo
    for table in root.iter('table'):
        
        # Passo 4: Extrair o tableName usando .get()
        table_name = table.get('tableName')

        # Passo 5: Comparar com a lista de busca fornecida
        if table_name in lista_busca:
            # Se deu match, salva o tableName
            tablenames_encontrados.add(table_name)

            # Extrai e salva o ossId e o id
            oss_id = table.get('ossId')
            t_id = table.get('id')

            if oss_id is not None:
                oss_ids_encontrados.add(oss_id)
            if t_id is not None:
                ids_encontrados.add(t_id)

    # Passo 6: Encontrar os tableNames que não existem no catálogo
    # Transforma a lista de busca em set e subtrai o que foi encontrado
    tabelas_faltantes = set(lista_busca) - tablenames_encontrados

    # Retorna o dicionário com todas as listas e sets solicitados
    return {
        'tablenames_encontrados': list(tablenames_encontrados),
        'oss_ids': oss_ids_encontrados,
        'ids': ids_encontrados,
        'tabelas_faltantes': list(tabelas_faltantes)
    }

# --- Como utilizar o script ---
if __name__ == "__main__":
    # Nome do catálogo client
    arquivo = 'HUAWEI_OSS_RAN_PM_SRAN_client.xml'

    # Lista de tableNames que você deseja pesquisar
    lista_de_tabelas = [
        'Tabela_Exemplo_1',
        'Tabela_Exemplo_2',
        'Tabela_Que_Nao_Existe'
    ]

    print(f"Iniciando busca no arquivo: {arquivo}")
    resultados = mapear_catalogos(arquivo, lista_de_tabelas)

    if resultados:
        print("\n--- Resultados do Mapeamento ---")
        print(f"TableNames encontrados: {resultados['tablenames_encontrados']}")
        print(f"ossIds (set): {resultados['oss_ids']}")
        print(f"IDs (set): {resultados['ids']}")
        print(f"TableNames NÃO encontrados: {resultados['tabelas_faltantes']}")