#!/usr/bin/env python

__doc__ = \
'''
	Medition_Events Performance CSV reader
'''

__version__ = '0.1'

__authors__ = [
				"Version 0.1: Francisco Santiago <francisco-j-santiago@telecom.pt>"
			]



import xml.etree.cElementTree as ET
import ast
import csv
import os
import re
import sys
import pprint
import datetime
import time
import json
from collections import OrderedDict
import importlib

# Local libraries
BaseOperator = importlib.import_module("shelf.collectorprocess.operators.BaseOperator").BaseOperator
FamilyObject = importlib.import_module("shelf.collectorprocess.operators.FamilyObject").FamilyObject
tools = importlib.import_module("shelf.collectorprocess.operators.tools")
logger = importlib.import_module("shelf.collectorprocess.logger").logger


class Operator(BaseOperator):

	#Class Constructor
	def __init__(self, operationParams, baseObject={}):
		BaseOperator.__init__(self, operationParams, baseObject=baseObject)
		self.lista_events= json.load(open('/opt/alticelabs/namf/src/shelf/collectorprocess/operators/Readers/NOKIA/CSV/ZABBIX/tableMapping.json'))


	def process(self, familyObj=FamilyObject(), baseObject={}):

		jsondata = json.load(open('/opt/alticelabs/namf/src/shelf/collectorprocess/operators/Readers/NOKIA/CSV/ZABBIX/config.json'), object_pairs_hook=OrderedDict)

		legend = []
		flag = True

		# guarda todos os warnings que a execucao gerou
		warninglist = set()

		# para evitar ter warnings repetidos
		warningskeys = list()

		# guarda todas as familias que estao configurados no JSON
		listkeys = jsondata.keys()
		rafa_dict=dict()

		filesToProcess = familyObj.getFiles()
		familyObj.clearDocuments()

		logger.debug("[Reader] Reading Zabbix Performance CSV files' contents...")

		#Ler do catalogo e tirar os ids por ordem de cada um deles
		#columnNamesList = self.lista_events #lista que vou ter obter do catalogo
		#nColumnNames = len(columnNamesList) #No final tem que ser 23
		for filePath in filesToProcess:
			tempdict={}
			newDict = {}
			#Get file's name to find the unitID
			fileName = os.path.basename(filePath)
			familyObj = FamilyObject()
			familyObj.fileName = fileName

			try:
				hostname = re.search('^#(.*)#', fileName).group(1)
				#ip=hostname
			except:
				hostname = ""
				logger.warning("IP Address was not found in file: \"{}\"".format(fileName))

			try:
				#Open file for writing
				f = open(filePath, 'r')
			except IOError:
				logger.warning("Could not open sample file \"{}\" in read mode: ".format(fileName))
				continue

			#Used to store the column names from the first line of each file
			nLine = 0
			i=0
			#Antes de utilizar o reader as cegas lembrar abrir o ficheiro para ver o sinal que utiliza o csv para separar as colunas
			for line in csv.reader(f,delimiter=',',quotechar='"', quoting=csv.QUOTE_ALL, skipinitialspace=True):
				tempdict = {}
				counters = []
				var = ""
				param_key = ""
				temp_value = ''
				sizejson = 0
				c = 0

				nLine += 1
				if not line:
					continue

				if nLine == 1:
					if len(line) == 0:
						logger.warning("No column names found in first line of file \"{0}\"".format(fileName))
						break
					columnNamesList = [ x.upper() for x in line ]
					nColumnNames = len(columnNamesList)
					continue

				if len(line) != nColumnNames:
					#print 'line '+ str(len(line))
					#print 'columnas' + str(nColumnNames)
					logger.warning("Number of values in line {0} is different than number of announced columns in sample \"{1}\"".format(nLine, fileName))
					continue

				startTime = line[0]
				startTime=datetime.datetime.strptime(startTime,"%d/%m/%Y %H:%M")
				startTime=datetime.datetime.strftime(startTime,"%Y-%m-%d %H:%M:%S")

				pattern = '%Y-%m-%d %H:%M:%S.%f'
				#Select the corresponding timestamp pattern
				if   re.match(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}$", startTime): pattern = '%Y-%m-%d %H:%M'
				elif re.match(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$", startTime): pattern = '%Y-%m-%d %H:%M:%S'
				elif re.match(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}.\d+$", startTime): pattern = '%Y-%m-%d %H:%M:%S.%f'

				#Try to match first timestamp with miliseconds
				interval = int(time.mktime(time.strptime(startTime, pattern)))

				hostid = line[1]
				# Type do item ID (MIN / MAX / AVG / value)
				mtype = line[4].split('-')[1]

				if '[' in line[6] and ']' in line[6]:
					#flagparentesis=True
					temp = line[6].split('[',1)
					key_dbn0 = temp[0]

					if key_dbn0 not in listkeys:
						if key_dbn0 not in warningskeys:
							warningskeys.append(key_dbn0)
							logger.warning("The Family [{0}] was not configured in config.json".format(key_dbn0))
						continue

					if key_dbn0 not in newDict.keys():
						newDict[key_dbn0] = OrderedDict()

					counters = temp[1].rsplit(']',1)[0]
					# regex para obter os contadores
					counters = re.split(""",(?=(?:(?:[^"]*'){.*})*[^"]*$)""", counters)

					# Campo que tem de ser concatenado
					try:
						param_concat_index = jsondata[key_dbn0]['concat']
						sizejson += 1
					except:
						param_concat_index = ''

					# Atributo que vai fazer parte da PK
					try:
						param_key_index = jsondata[key_dbn0]['param_key']
						sizejson += 1
					except:
						param_key_index = ''

					# adiciona "vazio" na posicao dos campos que nao estao preenchidos
					sizejson = len(jsondata[key_dbn0]) - sizejson
					while sizejson > len(counters):
						counters.append("")

					# contatena todos os atributos que vao fazer parte da PK do dicionario
					for temp in param_key_index:
						if counters[int(temp)] != '':
							param_key += '_' + counters[int(temp)]
						else:
							param_key += '_' + jsondata[key_dbn0].values()[int(temp)][""]



					# percorre todos os contadores/parametros
					for count in counters:
						tempdict = {}

						if count == '':
							try:
								var = temp_value + jsondata[key_dbn0].values()[c][""][mtype]
								value = line[8]
							except:
								try:
									var = temp_value + jsondata[key_dbn0].values()[c][mtype]
									value = line[8]
								except:
									var = temp_value + jsondata[key_dbn0].keys()[c]
									try:
										value = jsondata[key_dbn0].values()[c][""]
									except:
										value = jsondata[key_dbn0].values()[c]
						else:
							try:
								var = temp_value + jsondata[key_dbn0].values()[c][count][mtype]
								value = line[8]
							except:
								var = temp_value + jsondata[key_dbn0].keys()[c]
								value = count

						var = var.upper()
						# concatenar (ou nao) os atributos a PK e associar o valor
						# guarda a key (atributo) e o valor associado para preencher os campos
						if param_concat_index != '':
							if c == int(param_concat_index):
								temp_value = value+'_'
							else:
								temp_value = ''
								tempdict[var] = value
						else:
							tempdict[var] = value

						# A key do dicionario
						#keydict = startTime + '_' + hostid + '_' + key_dbn0 + param_key
						keydict = hostid + "_" + key_dbn0 + param_key

						# se ja existe a key no dicionario
						if keydict in newDict[key_dbn0]:
							newDict[key_dbn0][keydict].update(tempdict)
						# se ainda nao existe a key no dicionario
						else:
							newDict[key_dbn0][keydict] = OrderedDict()
							#data[keydict] = [] # update --> append
							newDict[key_dbn0][keydict].update({"STARTTIME": startTime}) #startTime
							newDict[key_dbn0][keydict].update({"HOSTID": hostid}) #hostID
							newDict[key_dbn0][keydict].update({"INTERVAL": interval}) #intervalID
							#newDict[key_dbn0][keydict].update({"IP": ip})
							#print str(fileName.rsplit("#",1)[0].replace("#","")), line[2].split('[')[0]

							# se a informacao do ip estiver presente
							if hostname:
								newDict[key_dbn0][keydict].update({"HOSTNAME": hostname + "-" + line[2].split('[')[0]}) #hostName
							else:
								newDict[key_dbn0][keydict].update({"HOSTNAME": line[2].split('[')[0]}) #hostName

							newDict[key_dbn0][keydict].update({"KEY": key_dbn0}) #id dbn0
							newDict[key_dbn0][keydict].update(tempdict)

						c += 1
				else:
					temp = line[6].rsplit('.',1)
					key_dbn0 = temp[0]


					# Verifica se a familia existe. Se nao existir nao trata esse caso
					if key_dbn0 not in listkeys:
						# Verifica se o warning ja foi lancado alguma vez
						if key_dbn0 not in warningskeys:
							warningskeys.append(key_dbn0)
							logger.warning("The Family [{0}] was not configured in config.json".format(key_dbn0))

						continue

					if key_dbn0 not in newDict.keys():
						newDict[key_dbn0] = OrderedDict()

					count = temp[1]

					try:
						var = jsondata[key_dbn0][count][str(mtype)]
					except:
						var = count

					var=var.upper()

					# Retirar string que vem entre [' e ']
					line[8] = line[8].replace("['","").replace("']","")
					if var != "HOSTNAME":
						tempdict[var] = line[8]

					# A key do dicionario
					#keydict = startTime + '_' + hostid + '_' + key_dbn0
					keydict = hostid + '_' + key_dbn0

					# se ja existe a key no dicionario
					if keydict in newDict[key_dbn0]:
						newDict[key_dbn0][keydict].update(tempdict)
					# se ainda nao existe a key no dicionario
					else:
						newDict[key_dbn0][keydict] = OrderedDict()
						#data[keydict] = [] # update --> append
						newDict[key_dbn0][keydict].update({"STARTTIME": startTime}) #startTime
						newDict[key_dbn0][keydict].update({"HOSTID": hostid}) #hostID
						newDict[key_dbn0][keydict].update({"INTERVAL": interval}) #intervalID
						#newDict[key_dbn0][keydict].update({"IP": ip})
						# se a informacao do ip estiver presente
						if hostname:
							newDict[key_dbn0][keydict].update({"HOSTNAME": hostname + "-" + line[2].split('[')[0]}) #hostName
						else:
							newDict[key_dbn0][keydict].update({"HOSTNAME": line[2].split('[')[0]}) #hostName

						newDict[key_dbn0][keydict].update({"KEY": key_dbn0}) #id dbn0
						newDict[key_dbn0][keydict].update(tempdict)

			rafa_dict=ast.literal_eval(json.dumps(newDict))
			for unit in rafa_dict:
				familyObj.clearDocuments()
				newFamilyObject=FamilyObject()
				newFamilyObject.fileName = familyObj.fileName
				newFamilyObject.setUnitID(unit)

				for document in rafa_dict[unit]:
					try:
						data_time = FamilyObject.parseEnvelopeDataTime(rafa_dict[unit][document]["STARTTIME"])
					except ValueError as e:
						logger.warning(
							"Could not build mediationEnvelope due to : {0}".format(
								e), __file__)
						continue
					data_document = {"dataTime": data_time, "granularitySec": 15, "data": rafa_dict[unit][document]}
					newFamilyObject.addDocument(data_document)

				self.nextOp(familyObj=newFamilyObject, baseObject=baseObject)
