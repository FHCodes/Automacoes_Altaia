import os

# Lista de servidores PM: (ID, IP)
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

# Template do arquivo YAML de configuração para PM
template = """host: "sftp://{{{{ip_omc}}}}"
local_path: "{{{{dest_path}}}}/{{{{ip_omc}}}}/{{{{date}}}}"
remote_path: "{{{{source_path}}}}/neexport_{{{{date}}}}/"

manual_ftp:
    mget_opts: "-d"
    remote_find_operations:
        - regex:
            search: "(A\\\\d{{8}}\\\\...00-\\\\d{{4}}-..15-\\\\d{{4}}.*\\\\.xml\\\\.gz|A\\\\d{{8}}\\\\...15-\\\\d{{4}}-..30-\\\\d{{4}}.*\\\\.xml\\\\.gz|A\\\\d{{8}}\\\\...30-\\\\d{{4}}-..45-\\\\d{{4}}.*\\\\.xml\\\\.gz|A\\\\d{{8}}\\\\...45-\\\\d{{4}}-..00-\\\\d{{4}}.*\\\\.xml\\\\.gz)"

skip_mirror_ftp: True

post_operations:
    - chmod_files:
        filters:
        - {{type: f}}
        mode: 0770
        src: '{{{{dest_path}}}}/{{{{ip_omc}}}}/{{{{date}}}}'

parameters:
    VENDOR: "HUAWEI"
    SOURCE_TYPE: "OSS"
    SOURCE_DOMAIN: "RAN"
    FUNCTION: "PM"
    SOURCE_SUBDOMAIN: "SRAN"
    MODEL: "OSS_RAN_PM_SRAN"
    LABEL: "HUAWEI OSS RAN PM SRAN VIVO - {server_name_upper}"
    SPEC: "3GPP_32_435"
    OSSVERSION: "20.1"
    PERIOD: 15
    HOST_ID: "{server_name_upper}"

filetime_extraction:
    regex: '.*/A(\\\\d{{8}})\\\\.(\\\\d{{2}}).*'
    regex_replacement: '\\\\g<1>\\\\g<2>'
    date_pattern: '%Y%m%d%H'
"""

# Geração dos arquivos de configuração PM
for srv_id, srv_ip in servidores:
    srv_upper = srv_id.upper()
    
    # Nome do arquivo seguindo o padrão PM
    filename = f"HUAWEI_OSS_RAN_PM_SRAN_VIVO_{srv_ip}.yml"
    
    # Preenche o template
    # Nota: Escapamos as barras invertidas da Regex para que o arquivo final saia correto
    content = template.format(server_name_upper=srv_upper)
    
    with open(filename, "w") as f:
        f.write(content)
    
    print(f"Config PM gerado: {filename}")