
# Objetivo pasta debug:

-> Criar localmente um cenario similar ao que existe na imagem, mas adaptando o output para permitir printar ou guardar o output em csv, em vez de enviar para kafka;

-> Alguns parsers possuem caminhos estaticos que precisam de ser atualizados conforme as diretorias locais onde se encontram os ficheiros;

-> Os artefactos de solucao necessarios devem ser colocados nas pastas respetivas:
collectors -> shelf/collectorprocess/collectors/specs
enrich -> shelf/collectorprocess/config/enrich
customizations -> shelf/collectorprocess/operators/Customizations
configs -> shelf/collectorprocess/config

-> Para printar os eventos, a spec deve incluir 'print="True"' em entrada de OutputManagers Kafka:
<operation type="OutputManagers" name="Kafka" print="True"/>

-> As configs em collectorprocess/config devem ser atualizadas conforme o necessario para existirem ligacoes a mongo, etc;

##########

# Execucao de teste com NAMF_PRODUCT_ORACLE (spec ja atualizada e no local necessario):

python mediation-parsers.py NAMF_PRODUCT "DATA\readertest" --out="DATA\csvoutput" --instance=3GPP --vendor=X --model=X --eventOriginId="23423" --parentEventId="777" --fetchTime="2018-03-05T11:52:28.426+00:00" --eventType="COLLECT" --sourceId="10.112.22.22" --hostId="hostName"





