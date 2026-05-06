import os
from lxml import etree

def buscar_ids_por_name():
    filename = "HUAWEI_OSS_RAN_PM_SRAN_oss.xml"
    
    # Sua lista de names exatos que vamos procurar
    lista_nomes = [
        "Algorithm Measurement 2 per Cell",
        "Algorithm Measurement per Cell",
        "BLER Measurement per Cell",
        "CBS Measurement per Cell",
        "CNOperator Measurement 2 per Cell",
        "CNOperator Measurement per Cell",
        "CPC Measurement",
        "CS RAB Modification Measurement per Cell",
        "CS RAB Setup Failure Measurement per Cell",
        "CS RAB Setup Measurement per Cell",
        "CS Service Quality Measurement per Cell",
        "Cell Algorithm Measurement",
        "Cell Power Measurement",
        "Cell Reserved Counter Measurement",
        "Cell Traffic Measurement",
        "Cell Update Measurement per Cell",
        "Common Channel Measurement per Cell",
        "Compressed Mode Measurement per Cell",
        "DCH Measurement",
        "EFACH Measurement",
        "EFACH Measurement per Cell",
        "EPCH Measurement per Cell",
        "ERACH Measurement",
        "ERACH Measurement per Cell",
        "ERACH Measurement per LoCell_SectorEQM",
        "ERACH Measurement per LoCell_SectorEQMGRP",
        "ExtendedCounter",
        "HSDPA Measurement",
        "HSDPA Measurement 2",
        "HSDPA Measurement per Cell",
        "HSUPA Measurement",
        "HSUPA Measurement per Cell",
        "Hard Handover Measurement per Cell",
        "Inter-RAT Handover Measurement per Cell",
        "Iu Signaling Connection Release Measurementper Cell",
        "Iub Interface Measurement per Cell",
        "Iub Measurement per LoCell_SectorEQM",
        "Iub Measurement per LoCell_SectorEQMGRP",
        "LCS Service Measurement per Cell",
        "Measurement of Channel Reconfiguration to DCH per Cell",
        "Measurement of SC APP Performance per Cell",
        "Multi-RAB Service Measurement per Cell",
        "NBIS Measurement per LoCell_SectorEQM",
        "PRACH Measurement",
        "PRACH Measurement per LoCell_SectorEQM",
        "PRACH Measurement per LoCell_SectorEQMGRP",
        "PS RAB Modification Measurement per Cell",
        "PS RAB Setup Failure Measurement per Cell",
        "PS RAB Setup Measurement per Cell",
        "PS Service Quality Measurement 2 per Cell",
        "PS service quality Measurement per Cell",
        "PTT Measurement per Cell",
        "Paging Measurement per Cell",
        "Parking Measurementper Cell",
        "QoS Measurement per Cell",
        "RAB Release Measurement per Cell",
        "RB Procedure Measurement per Cell",
        "RLC Measurement per Cell",
        "RRC Connection Reject Measurement per Cell",
        "RRC Connection Release Measurement per Cell",
        "RRC Connection Setup Measurement per Cell",
        "RRC MR Measurement per Cell",
        "RRC Status Measurement per Cell",
        "RTWP Measurement per LoCell_SectorEQM",
        "RTWP Measurement per LoCell_SectorEQMGRP",
        "Reserved Counter Measurement per Cell",
        "SCCPCH Measurement",
        "SPI Measurement per Cell",
        "Security Mode Measurement per Cell",
        "Soft Handover Measurement per Cell",
        "TX and RX Power Measurement per Cell",
        "Target SIR Measurement per Cell",
        "Traffic Measurement per Cell",
        "Traffic Volume and Data Rate Measurement per Cell",
        "UE Capability Measurement per Cell",
        "UL Interoperability Measurement per Cell",
        "UMTS Cell-to-UMTS Cell Handover Measurement",
        "URA Update Measurement per Cell",
        "Video Service Quality Measurement per Cell",
        "Voice Quality EVQI Measurement per Cell",
        "WLAN Measurement per Cell"
    ]

    print(f"🔍 Iniciando busca de IDs no arquivo: {filename}...")

    # Verifica se o arquivo existe
    if not os.path.exists(filename):
        print(f"❌ Erro: O arquivo '{filename}' não foi encontrado no diretório atual.")
        return

    resultados = {}

    try:
        # Carrega o XML
        parser = etree.XMLParser(remove_blank_text=False)
        tree = etree.parse(filename, parser)
        root = tree.getroot()

        # Busca todas as tags <unit>
        for unit in root.xpath("//*[local-name()='unit']"):
            unit_name = unit.get("name")
            unit_id = unit.get("id")
            
            # Se o name da unit estiver na nossa lista, salva o ID
            if unit_name in lista_nomes:
                resultados[unit_name] = unit_id

        # Relatório Final
        print("\n✅ Busca concluída!\n")
        print("📋 RELATÓRIO DE IDs ENCONTRADOS:")
        print("-" * 60)
        
        encontrados = 0
        
        # Imprime na mesma ordem da lista original para facilitar sua conferência
        for nome in lista_nomes:
            if nome in resultados:
                print(f"ID: {resultados[nome]:<12} | Name: {nome}")
                encontrados += 1
            else:
                print(f"ID: {'NÃO ACHOU':<12} | Name: {nome}")
                
        print("-" * 60)
        print(f"📊 Total de encontrados: {encontrados} de {len(lista_nomes)}")

    except Exception as e:
        print(f"⚠️ Erro ao processar o arquivo: {e}")

if __name__ == "__main__":
    buscar_ids_por_name()


#      RELATÓRIO DE IDs ENCONTRADOS:
# ------------------------------------------------------------
# ID: 82863958     | Name: Algorithm Measurement 2 per Cell
# ID: 67109391     | Name: Algorithm Measurement per Cell
# ID: 67109392     | Name: BLER Measurement per Cell
# ID: 67109389     | Name: CBS Measurement per Cell
# ID: 82864373     | Name: CNOperator Measurement 2 per Cell
# ID: 82863957     | Name: CNOperator Measurement per Cell
# ID: 50331653     | Name: CPC Measurement
# ID: 67109370     | Name: CS RAB Modification Measurement per Cell
# ID: 67109369     | Name: CS RAB Setup Failure Measurement per Cell
# ID: 67109368     | Name: CS RAB Setup Measurement per Cell
# ID: 82864100     | Name: CS Service Quality Measurement per Cell
# ID: 50331663     | Name: Cell Algorithm Measurement
# ID: 50331673     | Name: Cell Power Measurement
# ID: 50331665     | Name: Cell Reserved Counter Measurement
# ID: 50331650     | Name: Cell Traffic Measurement
# ID: 67109382     | Name: Cell Update Measurement per Cell
# ID: 82863959     | Name: Common Channel Measurement per Cell
# ID: 67109523     | Name: Compressed Mode Measurement per Cell
# ID: 50331662     | Name: DCH Measurement
# ID: 50331674     | Name: EFACH Measurement
# ID: 67109545     | Name: EFACH Measurement per Cell
# ID: 82863949     | Name: EPCH Measurement per Cell
# ID: 50331658     | Name: ERACH Measurement
# ID: 82863947     | Name: ERACH Measurement per Cell
# ID: 50331670     | Name: ERACH Measurement per LoCell_SectorEQM
# ID: 50331679     | Name: ERACH Measurement per LoCell_SectorEQMGRP
# ID: 82864403     | Name: ExtendedCounter
# ID: 50331648     | Name: HSDPA Measurement
# ID: 50331676     | Name: HSDPA Measurement 2
# ID: 67109390     | Name: HSDPA Measurement per Cell
# ID: 50331651     | Name: HSUPA Measurement
# ID: 67109471     | Name: HSUPA Measurement per Cell
# ID: 67109380     | Name: Hard Handover Measurement per Cell
# ID: 67109381     | Name: Inter-RAT Handover Measurement per Cell
# ID: 82864058     | Name: Iu Signaling Connection Release Measurementper Cell
# ID: 67109386     | Name: Iub Interface Measurement per Cell
# ID: 50331668     | Name: Iub Measurement per LoCell_SectorEQM
# ID: 50331677     | Name: Iub Measurement per LoCell_SectorEQMGRP
# ID: 67109510     | Name: LCS Service Measurement per Cell
# ID: 82864131     | Name: Measurement of Channel Reconfiguration to DCH per Cell
# ID: 82864312     | Name: Measurement of SC APP Performance per Cell
# ID: 67109377     | Name: Multi-RAB Service Measurement per Cell
# ID: 50331682     | Name: NBIS Measurement per LoCell_SectorEQM
# ID: 50331660     | Name: PRACH Measurement
# ID: 50331669     | Name: PRACH Measurement per LoCell_SectorEQM
# ID: 50331678     | Name: PRACH Measurement per LoCell_SectorEQMGRP
# ID: 67109374     | Name: PS RAB Modification Measurement per Cell
# ID: 67109373     | Name: PS RAB Setup Failure Measurement per Cell
# ID: 67109372     | Name: PS RAB Setup Measurement per Cell
# ID: 82864282     | Name: PS Service Quality Measurement 2 per Cell
# ID: 82864116     | Name: PS service quality Measurement per Cell
# ID: 82863953     | Name: PTT Measurement per Cell
# ID: 67109509     | Name: Paging Measurement per Cell
# ID: 82864101     | Name: Parking Measurementper Cell
# ID: 67109413     | Name: QoS Measurement per Cell
# ID: 67109376     | Name: RAB Release Measurement per Cell
# ID: 67109378     | Name: RB Procedure Measurement per Cell
# ID: 67109393     | Name: RLC Measurement per Cell
# ID: 67109367     | Name: RRC Connection Reject Measurement per Cell
# ID: 67109366     | Name: RRC Connection Release Measurement per Cell
# ID: 67109365     | Name: RRC Connection Setup Measurement per Cell
# ID: 67109384     | Name: RRC MR Measurement per Cell
# ID: 82834952     | Name: RRC Status Measurement per Cell
# ID: 50331672     | Name: RTWP Measurement per LoCell_SectorEQM
# ID: 50331680     | Name: RTWP Measurement per LoCell_SectorEQMGRP
# ID: 82863928     | Name: Reserved Counter Measurement per Cell
# ID: 50331661     | Name: SCCPCH Measurement
# ID: 82863914     | Name: SPI Measurement per Cell
# ID: 82864320     | Name: Security Mode Measurement per Cell
# ID: 67109379     | Name: Soft Handover Measurement per Cell
# ID: 67109385     | Name: TX and RX Power Measurement per Cell
# ID: 67109505     | Name: Target SIR Measurement per Cell
# ID: 67109387     | Name: Traffic Measurement per Cell
# ID: 67109508     | Name: Traffic Volume and Data Rate Measurement per Cell
# ID: 82864047     | Name: UE Capability Measurement per Cell
# ID: 82863927     | Name: UL Interoperability Measurement per Cell
# ID: 67109395     | Name: UMTS Cell-to-UMTS Cell Handover Measurement
# ID: 67109383     | Name: URA Update Measurement per Cell
# ID: 82864099     | Name: Video Service Quality Measurement per Cell
# ID: 82864097     | Name: Voice Quality EVQI Measurement per Cell
# ID: 82864053     | Name: WLAN Measurement per Cell
# ------------------------------------------------------------