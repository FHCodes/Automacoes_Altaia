import os
from lxml import etree

def remover_invcell_inteligente():
    # Nome do arquivo do catálogo de operações
    filename = "HUAWEI_OSS_RAN_PM_SRAN_operations.xml"
    
    # Sua lista de IDs
    ids_alvo = [
        "82863958", "67109391", "67109392", "67109389", "82864373",
        "82863957", "50331653", "67109370", "67109369", "67109368",
        "82864100", "50331663", "50331673", "50331665", "50331650",
        "67109382", "82863959", "67109523", "50331662", "50331674",
        "67109545", "82863949", "50331658", "82863947", "50331670",
        "50331679", "82864403", "50331648", "50331676", "67109390",
        "50331651", "67109471", "67109380", "67109381", "82864058",
        "67109386", "50331668", "50331677", "67109510", "82864131",
        "82864312", "67109377", "50331682", "50331660", "50331669",
        "50331678", "67109374", "67109373", "67109372", "82864282",
        "82864116", "82863953", "67109509", "82864101", "67109413",
        "67109376", "67109378", "67109393", "67109367", "67109366",
        "67109365", "67109384", "82834952", "50331672", "50331680",
        "82863928", "50331661", "82863914", "82864320", "67109379",
        "67109385", "67109505", "67109387", "67109508", "82864047",
        "82863927", "67109395", "67109383", "82864099", "82864097",
        "82864053"
    ]

    print(f"🧹 Iniciando a remoção inteligente do INVCELL no arquivo: {filename}...")
    unidades_modificadas = set()

    if not os.path.exists(filename):
        print(f"❌ Erro: O arquivo '{filename}' não foi encontrado no diretório atual.")
        return

    try:
        # Carrega o XML preservando a estrutura original e os comentários
        parser = etree.XMLParser(remove_blank_text=False)
        tree = etree.parse(filename, parser)
        root = tree.getroot()
        modificou_arquivo = False

        # Busca todas as tags <unit> no XML
        for unit in root.xpath("//*[local-name()='unit']"):
            unit_id = unit.get("id")
            
            # Se o ID da unit estiver na nossa lista alvo
            if unit_id in ids_alvo:
                # 1. Encontra a <operation> que POUCO IMPORTA onde, contém um <newField>INVCELL</newField>
                operacoes_com_invcell = unit.xpath(".//*[local-name()='operation'][.//*[local-name()='newField'][text()='INVCELL']]")
                
                for op in operacoes_com_invcell:
                    # 2. Conta quantos campos <newField> existem dentro dessa operação
                    todos_newfields = op.xpath(".//*[local-name()='newField']")
                    
                    if len(todos_newfields) == 1:
                        # Cenário A: Só existe o INVCELL. Arrancamos o bloco <operation> inteiro!
                        op.getparent().remove(op)
                    else:
                        # Cenário B: Existem outros <newField> (ex: CELL_NAME). Arrancamos APENAS a linha do INVCELL!
                        campo_invcell = op.xpath(".//*[local-name()='newField'][text()='INVCELL']")[0]
                        campo_invcell.getparent().remove(campo_invcell)
                        
                    unidades_modificadas.add(unit_id)
                    modificou_arquivo = True

        # Se fez alguma alteração, salva o arquivo sobrescrevendo-o
        if modificou_arquivo:
            tree.write(filename, encoding="utf-8", xml_declaration=True)
            print(f"✅ Arquivo {filename} salvo com sucesso!")
        else:
            print("ℹ️ Nenhuma tag/operação INVCELL precisou ser removida nos IDs especificados.")

    except Exception as e:
        print(f"⚠️ Erro ao processar o arquivo: {e}")

    # Relatório final
    print(f"\n📊 Total de units modificadas: {len(unidades_modificadas)} de {len(ids_alvo)} solicitadas.")
    
    if unidades_modificadas:
        print("\n📋 Lista de IDs das units onde a cirurgia ocorreu:")
        for u in sorted(unidades_modificadas):
            print(f"  - {u}")
            
        # Calcula e avisa se sobrou algum ID da lista que não foi achado/alterado
        nao_encontrados = set(ids_alvo) - unidades_modificadas
        if nao_encontrados:
            print(f"\n⚠️ Os seguintes IDs da sua lista NÃO sofreram alteração:")
            for n in sorted(nao_encontrados):
                print(f"  - {n}")

if __name__ == "__main__":
    remover_invcell_inteligente()