import os
from lxml import etree

def remover_item_invcell_oss():
    # Nome do arquivo alvo para o catálogo OSS
    filename = "HUAWEI_OSS_RAN_PM_SRAN_oss.xml"
    
    print(f"🧹 Iniciando a caçada e remoção do item INVCELL no arquivo: {filename}...")
    unidades_modificadas = set() # Usando set para evitar nomes duplicados na lista final

    # Verifica se o arquivo realmente está na pasta
    if not os.path.exists(filename):
        print(f"❌ Erro: O arquivo '{filename}' não foi encontrado no diretório atual.")
        return

    try:
        # Carrega o XML preservando a estrutura original e os comentários
        parser = etree.XMLParser(remove_blank_text=False)
        tree = etree.parse(filename, parser)
        root = tree.getroot()
        modificou_arquivo = False

        # Busca todas as tags <unit> ignorando problemas de namespace
        for unit in root.xpath("//*[local-name()='unit']"):
            tech = unit.get("tech")
            
            # Verifica se a unit é da tecnologia R2G ou R3G
            if tech in ["R2G", "R3G"]:
                # Busca a tag <item> que tenha id="INVCELL" ou name="INVCELL" dentro dessa <unit>
                itens_invcell = unit.xpath(".//*[local-name()='item'][@id='INVCELL' or @name='INVCELL']")
                
                for item in itens_invcell:
                    unit.remove(item) # Faz a remoção do <item> da árvore
                    unit_name = unit.get("name", "Desconhecido")
                    unidades_modificadas.add(unit_name)
                    modificou_arquivo = True

        # Se fez alguma alteração, salva o arquivo por cima do original
        if modificou_arquivo:
            tree.write(filename, encoding="utf-8", xml_declaration=True)
            print(f"✅ Arquivo {filename} salvo com sucesso!")
        else:
            print("ℹ️ Nenhum item INVCELL precisou ser removido (ou não foi encontrado nas units R2G/R3G).")

    except Exception as e:
        print(f"⚠️ Erro ao processar o arquivo: {e}")

    # Relatório final
    print(f"\n📊 Total de units únicas modificadas: {len(unidades_modificadas)}")
    
    if unidades_modificadas:
        print("\n📋 Lista de 'names' das units de onde o item INVCELL foi removido:")
        for u in sorted(unidades_modificadas):
            print(f"  - {u}")

if __name__ == "__main__":
    remover_item_invcell_oss()


#     📋 Lista de 'names' das units de onde o item INVCELL foi removido:
#   - Algorithm Measurement 2 per Cell
#   - Algorithm Measurement per Cell
#   - BLER Measurement per Cell
#   - CBS Measurement per Cell
#   - CNOperator Measurement 2 per Cell
#   - CNOperator Measurement per Cell
#   - CPC Measurement
#   - CS RAB Modification Measurement per Cell
#   - CS RAB Setup Failure Measurement per Cell
#   - CS RAB Setup Measurement per Cell
#   - CS Service Quality Measurement per Cell
#   - Cell Algorithm Measurement
#   - Cell Power Measurement
#   - Cell Reserved Counter Measurement
#   - Cell Traffic Measurement
#   - Cell Update Measurement per Cell
#   - Common Channel Measurement per Cell
#   - Compressed Mode Measurement per Cell
#   - DCH Measurement
#   - EFACH Measurement
#   - EFACH Measurement per Cell
#   - EPCH Measurement per Cell
#   - ERACH Measurement
#   - ERACH Measurement per Cell
#   - ERACH Measurement per LoCell_SectorEQM
#   - ERACH Measurement per LoCell_SectorEQMGRP
#   - ExtendedCounter
#   - HSDPA Measurement
#   - HSDPA Measurement 2
#   - HSDPA Measurement per Cell
#   - HSUPA Measurement
#   - HSUPA Measurement per Cell
#   - Hard Handover Measurement per Cell
#   - Inter-RAT Handover Measurement per Cell
#   - Iu Signaling Connection Release Measurementper Cell
#   - Iub Interface Measurement per Cell
#   - Iub Measurement per LoCell_SectorEQM
#   - Iub Measurement per LoCell_SectorEQMGRP
#   - LCS Service Measurement per Cell
#   - Measurement of Channel Reconfiguration to DCH per Cell
#   - Measurement of SC APP Performance per Cell
#   - Multi-RAB Service Measurement per Cell
#   - NBIS Measurement per LoCell_SectorEQM
#   - PRACH Measurement
#   - PRACH Measurement per LoCell_SectorEQM
#   - PRACH Measurement per LoCell_SectorEQMGRP
#   - PS RAB Modification Measurement per Cell
#   - PS RAB Setup Failure Measurement per Cell
#   - PS RAB Setup Measurement per Cell
#   - PS Service Quality Measurement 2 per Cell
#   - PS service quality Measurement per Cell
#   - PTT Measurement per Cell
#   - Paging Measurement per Cell
#   - Parking Measurementper Cell
#   - QoS Measurement per Cell
#   - RAB Release Measurement per Cell
#   - RB Procedure Measurement per Cell
#   - RLC Measurement per Cell
#   - RRC Connection Reject Measurement per Cell
#   - RRC Connection Release Measurement per Cell
#   - RRC Connection Setup Measurement per Cell
#   - RRC MR Measurement per Cell
#   - RRC Status Measurement per Cell
#   - RTWP Measurement per LoCell_SectorEQM
#   - RTWP Measurement per LoCell_SectorEQMGRP
#   - Reserved Counter Measurement per Cell
#   - SCCPCH Measurement
#   - SPI Measurement per Cell
#   - Security Mode Measurement per Cell
#   - Soft Handover Measurement per Cell
#   - TX and RX Power Measurement per Cell
#   - Target SIR Measurement per Cell
#   - Traffic Measurement per Cell
#   - Traffic Volume and Data Rate Measurement per Cell
#   - UE Capability Measurement per Cell
#   - UL Interoperability Measurement per Cell
#   - UMTS Cell-to-UMTS Cell Handover Measurement
#   - URA Update Measurement per Cell
#   - Video Service Quality Measurement per Cell
#   - Voice Quality EVQI Measurement per Cell
#   - WLAN Measurement per Cell