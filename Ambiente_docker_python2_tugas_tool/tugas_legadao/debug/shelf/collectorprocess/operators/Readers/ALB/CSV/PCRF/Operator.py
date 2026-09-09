#!/usr/bin/env python
__version__ = '1.0'

__doc__ = '''
            PCRF CSV to Mongo Reader
          '''

__authors__ = [
	"Version 1.0: Gil Martins <gil-l-martins@alticelabs.com>"
]

import os, json
import re
from datetime import datetime, timedelta
import importlib
from csv import reader
import pymongo

# Local libraries
BaseOperator = importlib.import_module("shelf.collectorprocess.operators.BaseOperator").BaseOperator
FamilyObject = importlib.import_module("shelf.collectorprocess.operators.FamilyObject").FamilyObject
logger = importlib.import_module("shelf.collectorprocess.logger").logger
mongoCon = importlib.import_module(
	"shelf.collectorprocess.operators.OutputManagers.Mongo.Operator").mongoConnection


class Operator(BaseOperator):

	# Class constructor
	def __init__(self, operationParams, baseObject={}):
		BaseOperator.__init__(self, operationParams, baseObject=baseObject)

		self.mongo_enrich_config = json.load(
			open('/opt/alticelabs/namf/src/shelf/collectorprocess/config/mongo_enrich_config.json'))

		self._collection_name = "PCRF_INSTANCES"

		self._mongoConnection = mongoCon(
			{"username": self.mongo_enrich_config["username"], "password": self.mongo_enrich_config["password"],
				"dbName": self.mongo_enrich_config["dbName"], "collectionName": self._collection_name,
				"connectionString": self.mongo_enrich_config["connectionString"]})
		self._directCon = self._mongoConnection.getConnection()

		# check if 'HOSTNAME' index already exists -> if not, creates it
		if 'HOSTNAME' not in [index['name'] for index in self._directCon.list_indexes()]:
			self._directCon.create_index([("HOSTNAME", pymongo.ASCENDING)], name='HOSTNAME')

	def process(self, familyObj=FamilyObject(), baseObject={}):
		logger.debug("[Reader] Reading CSV file' contents...", __file__)
		filesToBeProcessed = familyObj.getFiles()
		update_date = datetime.now()

		for filePath in filesToBeProcessed:
			familyObj.clearDocuments()
			fileName = os.path.basename(filePath)
			familyObj.fileName = fileName

			try:
				f = open(filePath, 'r')
			except IOError:
				logger.error(
					"Could not open sample file \"{0}\" in read mode: ".format(familyObj.fileName), __file__)
				continue

			mongo_header = ['OMSADDRESS', 'APPKEY', 'HOSTNAME', 'INSTANCE']
			header_list = []
			n_header_list = 0

			n_line = 0
			for line in reader(f, delimiter=';'):
				n_line += 1

				if n_line < 3:
					continue

				if n_line == 3:
					header_list = [x.upper() for x in line]
					n_header_list = len(header_list)
					continue

				if len(line) != n_header_list:
					logger.warning(
						"Number of values in line {0} is different than number of announced columns in sample \"{1}\"".format(
							n_line, familyObj.fileName), __file__)
					continue

				line = [value.strip() for value in line]
				document = dict(zip(header_list, line))

				mongo_document = {header: document[header] for header in mongo_header if header in document}

				try:
					mongo_document['CORRKEY'] = '#'.join(
						[mongo_document['APPKEY'], mongo_document['HOSTNAME'], mongo_document['INSTANCE']])
				except KeyError:
					logger.warning("Missing appkey, hostname or instance in line {0} of sample \"{1}\"".format(
						n_line, familyObj.fileName), __file__)
					continue

				self._mongoConnection.addBulkOperation(
					{"query":{"CORRKEY": mongo_document['CORRKEY']}, "set": mongo_document}, 'upSert')

		# clear non-updated documents
		date_to_clean = update_date - timedelta(hours=3)  # safe measure
		self._mongoConnection.addBulkOperation({'update': {"$lt": date_to_clean}}, 'remove')

		# execute bulk operations
		self._mongoConnection.executeBulkOperation()
