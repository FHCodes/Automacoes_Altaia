#!/usr/bin/env python
# -*- coding: utf-8 -*-

__doc__ = '''
    DENODO Reader Operator
'''

__version__ = '0.1'
__authors__ = [
    "Version 0.1: Felipe Henriques <felipe-s-henriques@openlabs.com.br>"
]

import os
import csv
import importlib
import re
from datetime import datetime, timedelta
from collections import defaultdict

# Local libraries
BaseOperator = importlib.import_module("shelf.collectorprocess.operators.BaseOperator").BaseOperator
FamilyObject = importlib.import_module("shelf.collectorprocess.operators.FamilyObject").FamilyObject
logger = importlib.import_module("shelf.collectorprocess.logger").logger


class Operator(BaseOperator):

    # -----------------------------
    # Construtor da classe
    # -----------------------------
    def __init__(self, operationParams, baseObject={}):
        # Chama o construtor da classe pai (BaseOperator)
        BaseOperator.__init__(self, operationParams, baseObject=baseObject)

    

    def normalize(self, text: str) -> str:
        """
        Normaliza nomes de métricas para o padrão do catálogo CLIENT (NAMF).

        Exemplos finais:
        - Packet loss dst->src average   -> PKTLOSS_DST_SRC_AVERAGE
        - Packet loss percentile (95)    -> PKTLOSS_PERCENTILE95
        """

        text = text.strip().upper()

        # Direções (todas as variações conhecidas)
        text = text.replace("DST->SRC", "DST_SRC")
        text = text.replace("SRC->DST", "SRC_DST")
        text = text.replace("DST_TO_SRC", "DST_SRC")
        text = text.replace("SRC_TO_DST", "SRC_DST")

        # Percentile 95
        text = text.replace("PERCENTILE_95", "PERCENTILE95")
        text = text.replace("PERCENTILE (95)", "PERCENTILE95")

        # Packet Loss (normaliza base)
        text = text.replace("PACKET LOSS", "PACKETLOSS")
        text = text.replace("PACKET_LOSS", "PACKETLOSS")

        # Limpeza de símbolos
        text = re.sub(r"[()%]", "", text)
        text = re.sub(r"\s+", "_", text)  # espaços viram underscore

        # Abreviação oficial
        text = re.sub(r"PACKETLOSS", "PKTLOSS", text)

        # 🔒 Garante underscores semânticos (evita "colado")
        # Ex: PKTLOSSDST -> PKTLOSS_DST
        text = re.sub(r"(PKTLOSS)(DST|SRC)", r"\1_\2", text)
        text = re.sub(r"(DST|SRC)(AVERAGE|PERCENTILE95)", r"\1_\2", text)

        # Remove underscores duplicados
        text = re.sub(r"_+", "_", text)

        return text.strip("_")


    # -----------------------------
    # Método principal de processamento
    # -----------------------------
    def process(self, familyObj=FamilyObject(), baseObject={}):
        logger.debug("Reading TWAMP TIM Inventory CSV file contents...", __file__)

        filePath = familyObj.getFiles()[0]
        familyObj.clearDocuments()

        fileName = os.path.basename(filePath)
        familyObj.fileName = fileName
        unit_id = "TWAMP_TIM_RAN"
        
        # Define o UnitID
        familyObj.setUnitID(unit_id)

        try:
            # ENCONTRA A LINHA DO CABEÇALHO PELO VALOR "NAME" NA COLUNA A
            with open(filePath, "r", encoding="latin-1", errors="replace") as f:

                linhas = f.readlines()

            for i, linha in enumerate(linhas):
                primeira_coluna = linha.split(";")[0].strip()
              
                if primeira_coluna.upper() == 'NAME':
                    linha_cabecalho = i
                    break

            if linha_cabecalho is None:
                raise Exception('Cabeçalho "NAME" não encontrado na coluna A')

            logger.debug(f"Cabeçalho encontrado na linha: {linha_cabecalho + 1}", __file__)
        
        except Exception as e:
                    logger.warning(f"Erro ao localizar o cabeçalho: {e}", __file__)

        
        # REABRE O ARQUIVO JÁ POSICIONADO NO CABEÇALHO 
        with open(filePath, "r", encoding="latin-1", errors="replace", newline="") as f: 
            
            for _ in range(linha_cabecalho):
                next(f)  # Pula as linhas de lixo

            csv_reader = csv.reader(f, delimiter=';', quotechar='"')

            # Lê o cabeçalho verdadeiro
            headers = [h.strip().upper() for h in next(csv_reader)]

            
            # Agrupamento por evento
            grupos = defaultdict(dict)

            for n_line, row in enumerate(csv_reader, start=1):

                # -------------------------
                # CAMPOS FIXOS
                # -------------------------
                name = row[0].strip()
                desc = row[1].strip()
                if_alias = row[2].strip()
                speed = row[3].strip()
                Signaling = row[8].strip()

                # -------------------------
                # DATA
                # -------------------------
                day = row[9].strip()
                month = row[10].strip()
                year = row[11].strip()
                hour = row[12].strip()

                try:
                    data_str = f"{day}/{month}/{year} {hour}"
                    date_obj = datetime.strptime(data_str, "%d/%m/%Y %H:%M")
                except ValueError:
                    # Data inválida
                    continue

                start_date = date_obj.strftime("%Y-%m-%d %H:%M:%S")

                # Chave única do evento
                chave = (name, desc, start_date)

                # -------------------------
                # INICIALIZA EVENTO
                # -------------------------
                if "Name" not in grupos[chave]:
                    grupos[chave]["NAME"] = name
                    grupos[chave]["DESCRIPTION"] = desc
                    grupos[chave]["IFALIAS"] = if_alias
                    grupos[chave]["SPEED"] = speed
                    grupos[chave]["STATTIME"] = start_date
                    grupos[chave]["GRANULARITYPERIOD"] = 1440
                    grupos[chave]["DAY"] = day
                    grupos[chave]["MONTH"] = month
                    grupos[chave]["YEAR"] = year
                    grupos[chave]["HOUR"] = hour
                    grupos[chave]["SIGNALING"] = Signaling

                    desc_parts = desc.split("|")
                    grupos[chave]["NE_NAME"] = desc_parts[0].strip() if len(desc_parts) > 0 else "" 
                    grupos[chave]["IPADDRESS"] = desc_parts[1].strip() if len(desc_parts) > 0 else ""
                    grupos[chave]["CONF"] = desc_parts[2].strip() if len(desc_parts) > 0 else ""
                    grupos[chave]["VENDOR"] = desc_parts[3].strip() if len(desc_parts) > 0 else ""
                    grupos[chave]["TECHNOLOGY"] = desc_parts[4].strip() if len(desc_parts) > 0 else ""


                # -------------------------
                # MÉTRICAS
                # -------------------------
                variable = row[4].strip()
                function = row[5].strip()
                raw_value = row[6].strip()

                metric_key = f"{self.normalize(variable)}_{self.normalize(function)}"

                # Trata valor numérico
                value = raw_value.replace(",", ".")
                try:
                    value = float(value)
                except ValueError:
                    pass

                # Evita sobrescrita silenciosa
                if metric_key not in grupos[chave]:
                    grupos[chave][metric_key] = value
                
        for evento in grupos.values():

            # DataTime no formato Altaia
            data_time = familyObj.parseEnvelopeDataTime(evento["STATTIME"])

            try:
                familyObj.addDocument({
                    "dataTime": data_time,
                    "granularitySec": int(evento["GRANULARITYPERIOD"]),
                    "data": evento
                })

                self.nextOp(
                    familyObj=familyObj,
                    baseObject=baseObject
                )

                familyObj.clearDocuments()

            except Exception as e:
               logger.warning(
                    "Unable to process {0} in unit {1} because wrong format => {2}".format(familyObj.fileName,familyObj.getUnitID(),e),
                    __file__
                    )


               

    