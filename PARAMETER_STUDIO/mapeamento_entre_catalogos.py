from lxml import etree

def mapear_tabelas(xml_path):
    info = {}
    
    # Carrega a estrutura do XML
    tree = etree.parse(xml_path)
    root = tree.getroot()

    # Itera sobre todas as tags <table> encontradas no XML
    for table in root.findall('.//table'):
        table_name = table.get('tableName')
        oss_id = table.get('ossId')
        table_id = table.get('id')

        # table_name como chave, (oss_id, table_id) como valor
        info[table_name] = (oss_id, table_id)

    return info