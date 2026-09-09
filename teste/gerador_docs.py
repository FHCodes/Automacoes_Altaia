import yaml
import os
from string import Template

def extrair_dados(data):
    # Caminhos base
    spec = data.get('spec', {})
    job_spec = spec.get('jobTemplate', {}).get('spec', {}).get('template', {}).get('spec', {})
    container = job_spec.get('containers', [{}])[0]
    res = container.get('resources', {})
    
    # Extração simples
    return {
        'nome': data.get('metadata', {}).get('name', 'N/A'),
        'schedule': spec.get('schedule', 'N/A'),
        'time_zone': spec.get('timeZone', 'N/A'),
        'concurrency': spec.get('concurrencyPolicy', 'N/A'),
        'deadline': spec.get('startingDeadlineSeconds', 'N/A'),
        'restart_policy': job_spec.get('restartPolicy', 'N/A'),
        'comando_full': " ".join(container.get('command', [])).replace('\n', ' '),
        'imagem': container.get('image', 'N/A'),
        'cpu_req': res.get('requests', {}).get('cpu', 'N/A'),
        'cpu_lim': res.get('limits', {}).get('cpu', 'N/A'),
        'mem_req': res.get('requests', {}).get('memory', 'N/A'),
        'mem_lim': res.get('limits', {}).get('memory', 'N/A'),
        'uid': container.get('securityContext', {}).get('runAsUser', 'N/A'),
        'runtime': job_spec.get('runtimeClassName', 'N/A'),
        'volumes_lista': "\n".join([f"  - {v.get('name')}" for v in job_spec.get('volumes', [])])
    }

# Setup da pasta de saída
pasta_saida = "documentacoes"
if not os.path.exists(pasta_saida):
    os.makedirs(pasta_saida)

with open('template.txt', 'r') as f:
    t = Template(f.read())

# Processar arquivos
for arquivo in os.listdir('.'):
    if arquivo.endswith(('.yaml', '.yml')):
        with open(arquivo, 'r') as f:
            data = yaml.safe_load(f)
            dados = extrair_dados(data)
            
            output_content = t.safe_substitute(dados)
            
            with open(os.path.join(pasta_saida, f"{dados['nome']}.txt"), 'w') as f_out:
                f_out.write(output_content)
                print(f"Gerado: {pasta_saida}/{dados['nome']}.txt")