from lxml import etree


def altera_operation_catalogo(nome_catalogo_operation, lista_operation_entity, lista_operation_todos, version):
    """
    lista_operation_entity: [(id, ["RNC_NAME", "NODEB_NAME", ...]), ...]
        -> gera o bloco <operation type="concatFields"> (lógica já existente)

    lista_operation_todos: [id, id, id, ...]
        -> gera o bloco <operation type="applyRegex"> com PS_VERSION (lógica nova)

    Um mesmo id pode aparecer nas duas listas, e nesse caso a unit recebe
    as duas estruturas.
    """

    output_path = nome_catalogo_operation

    print(f"[LOG] Iniciando alteração no catálogo Operation: {nome_catalogo_operation}")

    # 1. Transforma as listas em dicionários/sets para busca rápida
    mapa_operation_entity = {item[0]: item[1] for item in lista_operation_entity}
    set_operation_todos = set(lista_operation_todos)

    # 2. Carrega o XML
    parser = etree.XMLParser(remove_blank_text=True)
    tree = etree.parse(nome_catalogo_operation, parser)
    root = tree.getroot()

    # 3. Itera procurando apenas as tags <unit> que possuam o atributo 'id'
    for unit in root.findall('.//unit[@id]'):
        unit_id = unit.get('id')

        esta_em_entity = unit_id in mapa_operation_entity
        esta_em_todos = unit_id in set_operation_todos

        if not esta_em_entity and not esta_em_todos:
            continue

        # Garante que o pretty_print reformate essa unit corretamente,
        # mesmo que ela estivesse vazia (sem filhos) antes da alteração
        unit.text = None

        # ---------- Estrutura 1 (já existente): concatFields ----------
        if esta_em_entity:
            entity_fields = mapa_operation_entity[unit_id]

            if entity_fields:
                # Remove qualquer <operation type="concatFields"> que já exista
                # nessa unit (evita duplicar quando o script roda mais de uma vez)
                for op_existente in unit.findall('operation[@type="concatFields"]'):
                    unit.remove(op_existente)

                op_node = etree.SubElement(unit, 'operation', type="concatFields")
                def_node = etree.SubElement(op_node, 'def')

                indexes = [f"{{{i}}}" for i in range(len(entity_fields))]
                string_from = "/".join(indexes)
                def_node.set("stringfromfields", string_from)

                for field in entity_fields:
                    f_node = etree.SubElement(def_node, 'field')
                    f_node.text = field

                nf_node = etree.SubElement(def_node, 'newField')
                nf_node.text = "ENTITY_FIELD_VALUE"

        # ---------- Estrutura 2 (nova): applyRegex / PS_VERSION ----------
        if esta_em_todos:
            # Remove qualquer <item id="PS_VERSION"> que já exista nessa unit
            # (evita duplicar se o script rodar mais de uma vez)
            for item_existente in unit.findall('item[@id="PS_VERSION"]'):
                unit.remove(item_existente)

            item_node = etree.SubElement(unit, 'item', id="PS_VERSION")
            op_regex_node = etree.SubElement(item_node, 'operation', type="applyRegex")
            regex_node = etree.SubElement(op_regex_node, 'regex', pattern=f"{version}")
            nf_regex_node = etree.SubElement(regex_node, 'newField')
            nf_regex_node.text = "PS_VERSION"

    # 4. Salva o XML modificado
    tree.write(
        output_path,
        encoding='utf-8',
        xml_declaration=True,
        pretty_print=True
    )
    print(f"[SUCESSO] Catálogo Operation atualizado e salvo em: {output_path}")


# ==========================================
# Exemplo de como você vai chamar no seu código
# ==========================================
