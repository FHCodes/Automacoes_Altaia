from pathlib import Path

from lxml import etree
from parse_mapping_catalog import parse_catalog_xlsx
from mapeamento_entre_catalogos import mapear_tabelas
from altera_catalogo_oss import altera_oss
from altera_catalogo_operation import altera_operation_catalogo


def processa_catalogo(xml_path, mapping, info):
    # REMOVA as linhas do "with open" e "json.load"

    output_path = xml_path
    
    # O código já começa fazendo o parse do XML
    parser = etree.XMLParser(remove_blank_text=True)
    tree = etree.parse(xml_path, parser)
    root = tree.getroot()
    lista_oss = []
    lista_operation_entity = []
    lista_operation_todos = []

    version = next(iter(mapping.values()), {}).get("VERSION")

    # Iterar por todas as tags <table> do XML
    for table in root.findall('.//table'):
        table_name = table.get('tableName')

        if table_name in mapping:

            oss_id, id = info[table_name]

            entity = False

            table_map = mapping[table_name]

            if 'objectType' in table_map:
                table.set('ObjectType', table_map['objectType'])

            if 'dbn0Insert' in table_map:
                table.set('Dbn0Insert', str(table_map['dbn0Insert']).lower())

            columns_map = table_map.get('columns', {})
            entity_field_count = 0
            entity_field_col = None
            has_pk = False  

            for col in table.findall('column'):
                col_name = col.get('bdcolname')

                # Verifica se essa coluna é PK, independente de estar no columns_map
                if col.get('dbn0type') == 'PK':
                    has_pk = True

                if col_name in columns_map:
                    col_info = columns_map[col_name]

                    is_full_path = col_info.get('managedObjectFullPathField', False)
                    is_name = col_info.get('managedObjectNameField', False)

                    if is_full_path and is_name:
                        col.set('ExtraItemMeta', 'managedObjectNameField, managedObjectFullPathField')
                    elif is_name:
                        col.set('ExtraItemMeta', 'managedObjectNameField')
                    elif is_full_path:
                        col.set('ExtraItemMeta', 'managedObjectFullPathField')

                    if col_info.get('entityField', False):
                        entity_field_count += 1
                        entity_field_col = col

            # Regra: se tiver 2 ou mais -> cria ENTITY_FIELD_VALUE
            if entity_field_count >= 2:
                etree.SubElement(table, 'column', {
                    'bdcolname': 'ENTITY_FIELD_VALUE',
                    'bdtype': 'VARCHAR2(256)',
                    'dbn0type': 'ID',
                    'id': 'ENTITY_FIELD_VALUE',
                    'udn': 'entityFieldValue',
                    'ExtraItemMeta': 'entityField'
                })
                entity_fields = table_map.get('entityFields', [])
                lista_operation_entity.append((id, entity_fields))
                entity = True

            elif entity_field_count == 1 and entity_field_col is not None:
                existing = entity_field_col.get('ExtraItemMeta')
                if existing:
                    entity_field_col.set('ExtraItemMeta', f'{existing}, entityField')
                else:
                    entity_field_col.set('ExtraItemMeta', 'entityField')

            # Só executa se a tabela tiver pelo menos 1 coluna com dbn0type="PK"
            if has_pk:
                lista_operation_todos.append(id)
                lista_oss.append((oss_id, version, entity))

                etree.SubElement(table, 'column', {
                    'bdcolname': 'PS_VERSION',
                    'bdtype': 'VARCHAR2(256)',
                    'dbn0type': 'ID',
                    'id': 'PS_VERSION',
                    'udn': 'psVersion'
                })

    # 6. Salvar o novo XML modificado
    tree.write(
        output_path, 
        encoding='utf-8', 
        xml_declaration=True, 
        pretty_print=True
    )
    print(f"\n[SUCESSO] Arquivo XML atualizado e salvo em: {output_path}")

    return lista_oss, lista_operation_entity, lista_operation_todos, version

# ==========================================
# Como rodar:
# ==========================================
def articulador(client, oss, operation, caminho_planilha):
   
    # Chama a função e carrega o dicionário (JSON em memória) na variável documentacao
    documentacao = parse_catalog_xlsx(caminho_planilha)

    # Executa a função
    info = mapear_tabelas(client)  

    # Modifique os nomes dos arquivos conforme a sua pasta
    lista_oss, lista_operation_entity, lista_operation_todos, version = processa_catalogo(client, documentacao, info)

    altera_oss(oss, lista_oss)
    altera_operation_catalogo(operation, lista_operation_entity, lista_operation_todos, version)