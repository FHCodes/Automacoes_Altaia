import os
from lxml import etree
import datetime

def gerar_log_tabelas_ativas():
    diretorio_raiz = "catalogs_full"  # Ajuste para o diretório raiz onde estão os XMLs

    agora = datetime.datetime.now()
    arquivo_log = f"log_tabelas_ativas_{agora.strftime('%Y-%m-%d_%H-%M-%S')}.txt"
    
    print(f"🚀 Iniciando extração de log para: {arquivo_log}...")

    # Parser configurado para não quebrar com caracteres especiais
    parser = etree.XMLParser(remove_comments=False, strip_cdata=False)

    with open(arquivo_log, "w", encoding="utf-8") as log:
        log.write("--- RELATÓRIO DE TABELAS ATIVAS (EXCETO CM) ---\n\n")
        
        encontrou_geral = False

        for raiz, _, arquivos in os.walk(diretorio_raiz):
            for arquivo in arquivos:
                nome_low = arquivo.lower()
                
                
                # --- NOVO FILTRO INTELIGENTE ---
                # Só ignora se tiver "_CM_" ou "CM_" no nome, 
                # evitando barrar o NETCOMPASS por causa das letras C e M.
                if not nome_low.endswith(".xml") or "_client" not in nome_low:
                    continue
                
                # Ignora catálogos de Configuration Management (CM) especificamente
                if "_cm_" in nome_low:
                    continue
                # -------------------------------

                print(f"tabela analisada ---- {nome_low}")
                
                caminho_completo = os.path.join(raiz, arquivo)
                
                try:
                    tree = etree.parse(caminho_completo, parser)
                    root = tree.getroot()
                    
                    # Busca tabelas com active="TRUE"
                    tabelas_no_arquivo = []
                    for tabela in root.xpath(".//table"):
                        status = str(tabela.get("active", "")).strip().upper()
                        
                        if status == "TRUE":
                            t_name = tabela.get("tableName") or tabela.get("name")
                            if t_name:
                                tabelas_no_arquivo.append(t_name)

                    # Se o arquivo tiver tabelas ativas, escreve no log
                    if tabelas_no_arquivo:
                        encontrou_geral = True
                        log.write(f"{raiz} -- {arquivo}\n")
                        # Ordena as tabelas para o log ficar bonito
                        for t in sorted(set(tabelas_no_arquivo)):
                            log.write(f"- {t}\n")
                        log.write("\n") # Espaço entre arquivos
                    else:
                        log.write(f"{raiz} -- {arquivo} - Nenhuma tabela ativa encontrada.\n\n")
                        
                except Exception as e:
                    # Se der erro de parse, avisa no console mas segue o jogo
                    print(f"⚠️ Erro ao ler {arquivo}: {e}")
                    continue

        if not encontrou_geral:
            log.write("Nenhuma tabela ativa encontrada nos critérios informados.")

    print(f"✅ Log gerado com sucesso em: {arquivo_log}")

def ativar_todas_as_tabelas_de_cm():
    print(f"🧹 Iniciando ativação cirúrgica dos catálogos de CM (Preservando Comentários)...")
    arquivos_alterados = 0
    tabelas_ativadas_total = 0

    # O parser configurado com remove_comments=False garante que nada suma [cite: 907]
    parser = etree.XMLParser(remove_comments=False, strip_cdata=False)

    # os.walk(".") garante a recursividade total nas pastas de vendors [cite: 920, 986]
    for root_dir, _, files in os.walk("."):
        for filename in files:
            # Filtro para arquivos _client.xml que contenham CM no nome [cite: 966, 988]
            if "_client.xml" in filename and "_CM_" in filename.upper():
                path_completo = os.path.join(root_dir, filename)
                
                try:
                    # Carregamos o XML usando o parser que respeita comentários
                    tree = etree.parse(path_completo, parser)
                    root = tree.getroot()
                    foi_alterado = False
                    
                    # Procura todas as tags <table> em qualquer profundidade [cite: 935, 977]
                    for table in root.xpath(".//table"):
                        # Se não estiver TRUE (ignora espaços extras), a gente ativa 
                        status_atual = str(table.get("active", "")).strip().upper()
                        
                        if status_atual != "TRUE":
                            table.set("active", "TRUE")
                            foi_alterado = True
                            tabelas_ativadas_total += 1
                    
                    if foi_alterado:
                        # Salva mantendo a codificação UTF-8 e declaração XML [cite: 910, 984]
                        tree.write(
                            path_completo, 
                            encoding="utf-8", 
                            xml_declaration=True, 
                            pretty_print=False # Mantém a formatação original o máximo possível
                        )
                        print(f"✅ Tabelas ativadas e comentários preservados em: {path_completo}")
                        arquivos_alterados += 1
                        
                except Exception as e:
                    print(f"⚠️ Erro ao processar {path_completo}: {e}")

    if arquivos_alterados == 0:
        print("✅ Todas as tabelas de CM já estavam ativas")
        print("=====================================================================================")
        print("\n")
    
    else:

        print("\n--- PASSANDO TABELAS DE CM PARA TRUE ---")
        print(f"Arquivos XML processados e salvos: {arquivos_alterados}")
        print(f"Total de tabelas que passaram para active='TRUE': {tabelas_ativadas_total}")
        print("=====================================================================================")
        print("\n")

def desativar_todas_as_tabelas_pm():
    print(f"🧹 Iniciando desativação das tabelas de PM...")
    arquivos_alterados = 0
    tabelas_desativadas_total = 0

    # O parser com remove_comments=False garante que os comentários não virem "lixo" [cite: 929, 930]
    parser = etree.XMLParser(remove_comments=False, strip_cdata=False)

    # os.walk(".") garante a recursividade total nas pastas de vendors [cite: 1026]
    for root_dir, _, files in os.walk("."):
        for filename in files:
            # Filtro inteligente para processar apenas os catálogos [cite: 1028]
            if "_client.xml" in filename and not "_CM_" in filename.upper():
                path_completo = os.path.join(root_dir, filename)
                
                try:
                    # Carregamos o XML respeitando a estrutura original [cite: 927]
                    tree = etree.parse(path_completo, parser)
                    root = tree.getroot()
                    foi_alterado = False
                    
                    # Procura todas as tabelas usando XPath (mais preciso para catálogos complexos) [cite: 931]
                    for table in root.xpath(".//table"):
                        # Verificação "Anti-Sujeira": ignora espaços e trata maiúsculo/minúsculo [cite: 932, 933]
                        status_atual = str(table.get("active", "")).strip().upper()
                        
                        if status_atual != "FALSE":
                            table.set("active", "FALSE")
                            foi_alterado = True
                            tabelas_desativadas_total += 1
                    
                    if foi_alterado:
                        # Salva mantendo a codificação UTF-8 e declaração XML 
                        tree.write(
                            path_completo, 
                            encoding="utf-8", 
                            xml_declaration=True, 
                            pretty_print=False # Mantém a indentação original o máximo possível
                        )
                        print(f"🚫 Desativando tabelas em: {path_completo}")
                        arquivos_alterados += 1
                        
                except Exception as e:
                    print(f"⚠️ Erro ao processar {path_completo}: {e}")

    print("\n--- DESATIVANDO TODAS AS TABELAS DE PM ---")
    print(f"Arquivos XML limpos: {arquivos_alterados}")
    print(f"Total de tabelas marcadas como active='FALSE': {tabelas_desativadas_total}")
    print("=====================================================================================")
    print("\n")

def carregar_lista_tabelas(arquivo_txt):
    """Lê o TXT e retorna um set com os nomes das tabelas (limpos), ignorando comentários"""
    if not os.path.exists(arquivo_txt):
        print(f"❌ Erro: Arquivo {arquivo_txt} não encontrado.")
        return set()
    
    with open(arquivo_txt, 'r', encoding='utf-8') as f:
        tabelas = set()
        for line in f:
            linha_limpa = line.strip()
            # Só adiciona se a linha não estiver vazia e não começar com --
            if linha_limpa and not linha_limpa.startswith("--"):
                tabelas.add(linha_limpa)
        return set(tabelas)

def ativa_tabelas_pm_da_lista(tabelas_alvo):
    print(f"🚀 Iniciando busca cirúrgica por arquivos _client.xml (Preservando Comentários)...")
    arquivos_alterados = 0
    tabelas_ativadas_total = 0
    tabelas_nao_modificadas = []

    # O parser configurado com remove_comments=False é o "pulo do gato" [cite: 2012]
    parser = etree.XMLParser(remove_comments=False, strip_cdata=False)

    # os.walk(".") garante a recursividade total em todas as pastas de vendors [cite: 3684]
    for root_dir, _, files in os.walk("."):
        for filename in files:
            # Filtro inteligente para focar apenas nos catálogos de cliente
            if "_client.xml" in filename and not "_CM_" in filename.upper():
                path_completo = os.path.join(root_dir, filename)
                
                try:
                    # Carregamos o XML usando o parser que respeita a estrutura original
                    tree = etree.parse(path_completo, parser)
                    root = tree.getroot()
                    foi_alterado = False

                    # Procura todas as tags <table> (uso de XPath para maior precisão) [cite: 2014]
                    for table in root.xpath(".//table"):
                        # Captura o nome da tabela (tableName)
                        table_name_xml = table.get("tableName")

                        # Se a tabela estiver na sua lista alvo (TXT) [cite: 3687, 3688]
                        if table_name_xml in tabelas_alvo:
                            # Verificação "Anti-Sujeira": ignora espaços e trata maiúsculo/minúsculo 
                            status_atual = str(table.get("active", "")).strip().upper()
                            
                            if status_atual != "TRUE":
                                table.set("active", "TRUE")
                                foi_alterado = True
                                tabelas_ativadas_total += 1

                            else:
                                tabelas_nao_modificadas.append(table_name_xml)

                    # Salva o arquivo apenas se houve alteração real [cite: 2004]
                    if foi_alterado:
                        # Mantém o encoding UTF-8 e a declaração XML (crucial para o Kubernetes) 
                        tree.write(
                            path_completo, 
                            encoding="utf-8", 
                            xml_declaration=True, 
                            pretty_print=False # Tenta manter a indentação original
                        )
                        print(f"✅ Atualizado e comentários preservados: {path_completo}")
                        arquivos_alterados += 1

                except Exception as e:
                    print(f"⚠️ Erro ao processar {path_completo}: {e}")

    print("\n--- PASSANDO TABELAS DE PM PARA TRUE ---")
    print(f"Arquivos XML modificados: {arquivos_alterados}")
    print(f"Total de tabelas que passaram para active='TRUE': {tabelas_ativadas_total}")
    print()
    print(f"Esses {len(tabelas_nao_modificadas)} arquivos não tiveram tabelas para serem modificadas pra active:TRUE)")
    for tabela in tabelas_nao_modificadas:
        print(f"❌{tabela}")
    print("=====================================================================================")
    print("\n")

if __name__ == "__main__":

    print("[1] - Ativar todas as yabelas de CM e as de PM que estão na lista de tabelas")
    print("[2] - Gerar log de tabelas que estão ativas")
    resp = int(input())

    if resp == 1:
        desativar_todas_as_tabelas_pm()
        ativar_todas_as_tabelas_de_cm()
        
        lista_tabelas = carregar_lista_tabelas("tabelas_ativas.txt")
        
        if lista_tabelas:
            print(f"📋 {len(lista_tabelas)} tabelas carregadas do TXT.")
            ativa_tabelas_pm_da_lista(lista_tabelas)
        else:
            print("🛑 Nenhuma tabela para processar. Encerrando.")
        gerar_log_tabelas_ativas()
    elif resp == 2:
        gerar_log_tabelas_ativas()