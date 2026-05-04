import os

# Lista de servidores CM: (ID, IP)
servidores = [
    ("rjbar-taihua-ssv31", "10.43.86.6"),
    ("rjbar-taihua-ssv32", "10.43.86.7"),
    ("rjbar-taihua-ssv33", "10.43.86.8"),
    ("rjbar-taihua-ssv34", "10.43.86.9"),
    ("rjbar-taihua-ssv35", "10.43.86.10"),
    ("rjbar-taihua-ssv36", "10.43.86.11"),
    ("rjbar-taihua-ssv37", "10.43.86.12"),
    ("rjbar-taihua-ssv38", "10.43.86.13"),
]

# Template do arquivo YAML de configuração
template = """host: "sftp://{{{{ip_omc}}}}"
local_path: "{{{{dest_path}}}}/{{{{ip_omc}}}}/{{{{date}}}}"
remote_path: "{{{{source_path}}}}"

manual_ftp:
    mget_opts: "-d"
    remote_find_operations:
        - regex:
            search: 'GExport_(BSC|RNC|M|T|S|W).*_{{{{date}}}}.*\\.xml\\.gz'

skip_mirror_ftp: True

post_operations:
    - chmod_files:
        filters:
        - {{type: f}}
        mode: 0770
        src: '{{{{dest_path}}}}/{{{{ip_omc}}}}/{{{{date}}}}'

parameters:
    SOURCE_TYPE: "OSS"
    SOURCE_DOMAIN: "RAN"
    SOURCE_SUBDOMAIN: "SRAN"
    MODEL: "OSS_RAN_CM_SRAN"
    VENDOR: "HUAWEI"
    LABEL: "HUAWEI OSS RAN CM SRAN VIVO - {server_name_upper}"
    FUNCTION: "CM"
    SPEC: "GEXPORT"
    OSSVERSION: "20.1"
    PERIOD: 1440
    HOST_ID: "{server_name_upper}"
"""

# Geração dos arquivos de configuração
for srv_id, srv_ip in servidores:
    # Nome do servidor em maiúsculo para o LABEL e HOST_ID
    srv_upper = srv_id.upper()
    
    # Nome do arquivo final
    filename = f"HUAWEI_OSS_RAN_CM_SRAN_VIVO_{srv_ip}.yml"
    
    # Preenche o template
    # Nota: Usamos as chaves duplas no template para escapar as variáveis do Jinja2/Ansible
    content = template.format(server_name_upper=srv_upper)
    
    with open(filename, "w") as f:
        f.write(content)
    
    print(f"Config gerado: {filename}")