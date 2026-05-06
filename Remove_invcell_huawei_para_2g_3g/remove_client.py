import os
from lxml import etree

def remover_coluna_invcell_huawei():
    # Nome do arquivo exato que você passou
    filename = "HUAWEI_OSS_RAN_PM_SRAN_client.xml"
    
    print(f"🧹 Iniciando a caçada e remoção da coluna INVCELL no arquivo: {filename}...")
    tabelas_modificadas = set()

    # Verifica se o arquivo realmente está na pasta antes de tentar abrir
    if not os.path.exists(filename):
        print(f"❌ Erro: O arquivo '{filename}' não foi encontrado no diretório atual.")
        return

    try:
        # Carrega o XML preservando a estrutura e comentários
        parser = etree.XMLParser(remove_blank_text=False)
        tree = etree.parse(filename, parser)
        root = tree.getroot()
        modificou_arquivo = False

        # Busca todas as tags <table> ignorando namespaces
        for table in root.xpath("//*[local-name()='table']"):
            tech = table.get("tech")
            
            # Verifica se a tabela é R2G ou R3G
            if tech in ["R2G", "R3G"]:
                # Busca colunas que tenham o bdcolname ou id igual a INVCELL
                colunas_invcell = table.xpath(".//*[local-name()='column'][@bdcolname='INVCELL' or @id='INVCELL']")
                
                for column in colunas_invcell:
                    table.remove(column) # Remove a tag <column> da árvore
                    table_name = table.get("tableName", "Desconhecido")
                    tabelas_modificadas.add(table_name)
                    modificou_arquivo = True

        # Se achou e removeu algo, salva o arquivo sobrescrevendo-o
        if modificou_arquivo:
            tree.write(filename, encoding="utf-8", xml_declaration=True)
            print(f"✅ Arquivo {filename} salvo com as alterações!")
        else:
            print("ℹ️ Nenhuma coluna INVCELL precisou ser removida (ou já não existia nas tabelas R2G/R3G).")

    except Exception as e:
        print(f"⚠️ Erro ao processar o arquivo: {e}")

    # Relatório final
    print(f"\n📊 Total de tabelas únicas modificadas: {len(tabelas_modificadas)}")
    
    if tabelas_modificadas:
        print("\n📋 Lista de tableNames onde a coluna INVCELL foi removida:")
        for t in sorted(tabelas_modificadas):
            print(f"  - {t}")

if __name__ == "__main__":
    remover_coluna_invcell_huawei()



#     📋 Lista de tableNames onde a coluna INVCELL foi removida:
#   - T50331648
#   - T50331650
#   - T50331651
#   - T50331653
#   - T50331658
#   - T50331660
#   - T50331661
#   - T50331662
#   - T50331663
#   - T50331665
#   - T50331668
#   - T50331669
#   - T50331670
#   - T50331672
#   - T50331673
#   - T50331674
#   - T50331676
#   - T50331677
#   - T50331678
#   - T50331679
#   - T50331680
#   - T50331682
#   - T67109365
#   - T67109366
#   - T67109367
#   - T67109368
#   - T67109369
#   - T67109370
#   - T67109372
#   - T67109373
#   - T67109374
#   - T67109376
#   - T67109377
#   - T67109378
#   - T67109379
#   - T67109380
#   - T67109381
#   - T67109382
#   - T67109383
#   - T67109384
#   - T67109385
#   - T67109386
#   - T67109387
#   - T67109389
#   - T67109390
#   - T67109391
#   - T67109392
#   - T67109393
#   - T67109395
#   - T67109413
#   - T67109471
#   - T67109505
#   - T67109508
#   - T67109509
#   - T67109510
#   - T67109523
#   - T67109545
#   - T82834952
#   - T82863914
#   - T82863927
#   - T82863928
#   - T82863947
#   - T82863949
#   - T82863953
#   - T82863957
#   - T82863958
#   - T82863959
#   - T82864047
#   - T82864053
#   - T82864058
#   - T82864097
#   - T82864099
#   - T82864100
#   - T82864101
#   - T82864116
#   - T82864131
#   - T82864282
#   - T82864312
#   - T82864320
#   - T82864373
#   - T82864403