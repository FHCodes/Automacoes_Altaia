#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__doc__ = '''
    ACCEDIAN TWAMP Reader Operator
'''

__version__ = '0.1'
__authors__ = [
    "Version 0.1: Felipe Henriques <felipe-s-henriques@openlabs.com.br>"
]

import os
import csv
import importlib
import re
from datetime import datetime, timedelta, timezone
import zoneinfo  # Disponível no Python 3.9+

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


    def unix_to_sao_paulo(self, ms_timestamp):
        # Converte de milissegundos para segundos
        ts_seconds = ms_timestamp / 1000
        
        # Converte para UTC
        dt_utc = datetime.fromtimestamp(ts_seconds, tz=timezone.utc)
        
        # Converte para São Paulo
        sao_paulo_tz = zoneinfo.ZoneInfo("America/Sao_Paulo")
        dt_sp = dt_utc.astimezone(sao_paulo_tz)
        
        return dt_sp
    
    # -----------------------------
    # Método principal de processamento
    # -----------------------------
    def process(self, familyObj=FamilyObject(), baseObject={}):
        # Loga o início do processamento
        logger.debug("Reading ACCEDIAN TWAMP CSV file contents...", __file__)

        # Obtém o caminho do arquivo a ser processado
        filePath = familyObj.getFiles()[0]

        # Limpa documentos antigos no objeto
        familyObj.clearDocuments()

        # Extrai apenas o nome do arquivo
        fileName = os.path.basename(filePath)
        familyObj.fileName = fileName
        

        try:
            # Abre o arquivo CSV
            with open(filePath, 'r', encoding='utf-8') as f:
                csv_reader = csv.reader(f, delimiter=',')

                # Lê o cabeçalho (primeira linha)
                headers = next(csv_reader)

                # Itera sobre cada linha do CSV
                for n_line, row in enumerate(csv_reader):

                    # Monta o dicionário com os campos
                    document = dict((headers[i].upper(), value) for i, value in enumerate(row) if i < len(headers))

                    data_time = None

                    try:
                        # Gera timestamp interno (do envelope)
                        data_time = self.unix_to_sao_paulo(float(document["STATTIME"]))
                        # print (data_time) # Mantenha se for útil para debug, remova na produção
                    
                    except (ValueError, KeyError) as e:
                        # Loga o erro de forma clara, informando qual linha e erro ocorreu
                        logger.warning(
                            "Ocorreu um erro ao processar a data na linha {0} - Erro: {1}".format(n_line + 2, e), 
                            __file__
                        )
                        continue

                    # Adiciona o documento processado
                    familyObj.addDocument({
                        "dataTime": data_time,
                        "granularitySec": int(document["INTERVAL"]),
                        "data": document
                    })

                    # Chama o próximo operador do pipeline
                    self.nextOp(familyObj=familyObj, baseObject=baseObject)

                    # Limpa documentos temporários
                    familyObj.clearDocuments()

        except Exception as e:
            # Captura e loga qualquer erro geral no processamento
            logger.warning(
                "Unable to process {0} in unit {1} because wrong format => {2}".format(
                    familyObj.fileName,
                    familyObj.getUnitID(),
                    e
                ),
                __file__
            )
