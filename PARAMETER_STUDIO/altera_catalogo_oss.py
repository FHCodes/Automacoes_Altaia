from lxml import etree

def altera_oss(nome_catalogo_oss, lista_oss):
    """
    lista_oss deve ser uma lista de tuplas/listas no formato:
    [(oss_id, version, entity_boolean), ...]
    """

    output_path = nome_catalogo_oss
    
    print(f"[LOG] Iniciando alteração no catálogo OSS: {nome_catalogo_oss}")

    # 1. Transforma a lista num dicionário para busca ultra-rápida.
    # Chave: oss_id | Valor: (version, entity)
    mapa_oss = {item[0]: (item[1], item[2]) for item in lista_oss}

    # 2. Carrega o XML
    parser = etree.XMLParser(remove_blank_text=True)
    tree = etree.parse(nome_catalogo_oss, parser)
    root = tree.getroot()

    # 3. Itera procurando as tags que possuam ossId (no seu caso, as tags <unit>)
    for unit in root.findall('.//*[@ossId]'):
        oss_id = unit.get('ossId')

        # Verifica se achou esse ossId na nossa lista
        if oss_id in mapa_oss:
            versao, entity = mapa_oss[oss_id]
            
            # Formata a versão para o padrão v="20.1/20.1"
            versao_str = versao if versao else "Nao_informado"
            valor_v = f"{versao_str}/{versao_str}"

            # REGRA 1: Se entity == True, insere o ENTITY_FIELD_VALUE primeiro
            if entity:
                etree.SubElement(unit, 'item', {
                    'desc': 'ENTITY_FIELD_VALUE',
                    'id': 'ENTITY_FIELD_VALUE',
                    'name': 'ENTITY_FIELD_VALUE',
                    'typeCust': 'STRING',
                    'typeVendor': 'STRING',
                    'unitVendor': 'STRING',
                    'v': valor_v,
                    'seqlength': 'Single'
                })

            # REGRA 2: Independente do entity, o PS_VERSION sempre entra (se for false, entra SÓ ele)
            etree.SubElement(unit, 'item', {
                'desc': 'PS_VERSION',
                'id': 'PS_VERSION',
                'name': 'PS_VERSION',
                'typeCust': 'STRING',
                'typeVendor': 'STRING',
                'unitVendor': 'String',
                'v': valor_v,
                'seqlength': 'Single'
            })

    # 4. Salva o XML modificado
    tree.write(
        output_path, 
        encoding='utf-8', 
        xml_declaration=True, 
        pretty_print=True
    )
    print(f"[SUCESSO] Catálogo OSS atualizado e salvo em: {output_path}")


# ==========================================
# Exemplo de como você vai chamar no seu código
# ==========================================
