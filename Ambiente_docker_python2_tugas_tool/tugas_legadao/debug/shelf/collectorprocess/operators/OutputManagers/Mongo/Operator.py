#!/usr/bin/env python

__doc__ = \
"""
	Mongo Operator
	This module is responsible for the intercommunication between Parsers and MongoDB
"""

__version__ = '0.2'

__authors__ = [
	"Version 0.1: Bruno Silva <bruno-e-silva@alticelabs.com>"
	"Version 0.2: Paulo Gil <paulo-a-gil@alticelabs.com>"
]

# Native libraries
import importlib
import pymongo
from datetime import datetime

# Local libraries
logger = importlib.import_module("shelf.collectorprocess.logger").logger
ConnectionFactory = importlib.import_module("shelf.collectorprocess.operators.ConnectionFactory").ConnectionFactory

class mongoConnection(ConnectionFactory):

	def __init__(self, config):
		ConnectionFactory.__init__(self)
		self._con = None
		self._connectionString = config['connectionString']
		self._username = config['username']
		self._password = config['password']
		self._instancesDBName = config['dbName']
		self._collectionName = config['collectionName']
		self._indexes = (config['indexes'] if 'indexes' in config else list())
		self._bulkOperations = None

	def getConnection(self, writeConcern=1):
		con = None
		try:
			try:
				con = pymongo.MongoClient(self._connectionString, w=writeConcern)
			except AttributeError:
				logger.error(("MongoDB connection information [hostname|user|pass] must be provided for the Enrichment operator"))
				return
			except pymongo.errors.ConnectionFailure, e:
				logger.error(("MongoDB connection failed using the provided information [hostname|user|pass]"))
				return
			except pymongo.errors.OperationFailure, e:
				logger.error(str(e))

			db = con[self._instancesDBName]
			if self._username != "" and self._password != "":
				db.authenticate(self._username, self._password)

			self._con = db[self._collectionName]

		except KeyError as e:
			logger.error("Attribute collection {0} is missing from request and is mandatory for this pack".format(str(self._collectionName)))
			return
		except Exception as e:
			logger.error("Mongo setup failed due to {}".format(e))
			return

		try:
			for index in self._indexes:
				self._con.create_index(list(index['keys'].items()),name=index['name'])
		except Exception as e:
			logger.error("Mongo index creating failed due to {}".format(e))

		# Init unordered bulk operation
		self._bulkOperations = self._con.initialize_unordered_bulk_op()

		return self._con

	def executeQuery(self, query, action=None):
		try:
			if action == 'find_one':
				return self._con.find_one(query)
			if action == 'find':
				return self._con.find(query)
			if action == 'insert':
				return self._con.insert(query)
			if action == 'upSert':
				query['set']['update'] = datetime.now()
				return self._con.update(query['query'], {"$set": query['set']}, upsert=True)
			if action == 'update':
				query['set']['update'] = datetime.now()
				return self._con.update(query['query'], {"$set": query['set']})
			if action == 'remove':
				return self._con.remove(query)
		except Exception as e:
			logger.warning(self._con)
			logger.warning(e)
			return
		logger.warning('Query action {:s} not known.'.format(action))
		return

	def addBulkOperation(self, query, action=None):
		try:
			if action == 'insert':
				self._bulkOperations.insert(query)
			elif action == 'update':
				query['set']['update'] = datetime.now()
				self._bulkOperations.insert(query['query']).update({"$set": query['set']})
			elif action == 'upSert':
				query['set']['update'] = datetime.now()
				self._bulkOperations.find(query['query']).upsert().update({"$set": query['set']})
			elif action == 'remove':
				self._bulkOperations.find(query).remove()
			else:
				logger.warning('Query action {:s} not known.'.format(action))
			return
		except Exception as e:
			logger.warning(self._con)
			logger.warning(e)
			return

	def executeBulkOperation(self):
		try:
			self._bulkOperations.execute()
		except Exception as e:
			logger.warning('Bulk execution failed due to: {0}'.format(e))

		self._bulkOperations = self._con.initialize_unordered_bulk_op()
		return
