__doc__ = \
	__version__ = '1.0'
__authors__ = ['Version 0.1: Bruno Silva <bruno-e-silva@alticelabs.com>']

from lib.objects.generic.baseType import baseType
from collections import OrderedDict
from lib.Logger import Logger
from lib.objects.generic.extraTag import extraTag


class unit(baseType):

	def __init__(self):
		baseType.__init__(self)
		self._ossId = ''
		self._typeId = ''
		self._tables = dict()
		self._attributes = OrderedDict()
		self._bdcolnames = list()
		self._measuredObject = ''
		self._numberOfAttributes = 0
		self._hierarchyList = dict()
		self._createHierarchy = True
		self._operations = dict()
		self._tech = ''
		self._desc = ''
		self._name = ''
		self._structDependencies = list()
		self._size = 0
		self._isDummy = False

	def create(self, ossId, typeId, name, desc, measuredObject):
		self._ossId = ossId
		self._typeId = typeId
		self._measuredObject = measuredObject
		self._name = name
		self._desc = desc

	@property
	def isDummy(self):
		return self._isDummy
	@isDummy.setter
	def isDummy(self, value):
		self._isDummy = value
	def setDummy(self):
		self._isDummy = True


	@property
	def bdcolnames(self):
		return self._bdcolnames
	@bdcolnames.setter
	def bdcolnames(self, value):
		self._bdcolnames = value

	@property
	def structDependencies(self):
		return self._structDependencies
	@structDependencies.setter
	def structDependencies(self, value):
		self._structDependencies = value
	def addStructDependencie(self, value):
		self._structDependencies.append(value)

	@property
	def ossId(self):
		return self._ossId
	@ossId.setter
	def ossId(self, value):
		self._ossId = value

	@property
	def tech(self):
		return self._tech
	@tech.setter
	def tech(self, value):
		self._tech = value

	@property
	def measuredObject(self):
		return self._measuredObject
	@measuredObject.setter
	def measuredObject(self, value):
		self._measuredObject = value

	@property
	def createHierarchy(self):
		return self._createHierarchy
	def activeHierarchy(self):
		self._createHierarchy = True
	def disableHierarchy(self):
		self._createHierarchy = False

	@property
	def size(self):
		return self._size
	@size.setter
	def size(self, value):
		self._size = value

	@property
	def hierarchyList(self):
		return self._hierarchyList
	def addHierarchy(self, hierarchy, value):
		#if hierarchy not in self._hierarchyList:
		self._hierarchyList[hierarchy] = value
		#else:
		#	self._hierarchyList[hierarchy].append(value)
	def removeHierarchy(self, hierarchy):
		del self._hierarchyList[hierarchy]
	def setHierarchy(self, hierarchyList):
		self._hierarchyList = hierarchyList
	def addHierarchies(self, hierarchyData):
		for pattern in hierarchyData.keys():
			if pattern in self._hierarchyList.keys():
				self._hierarchyList[pattern].append(hierarchyData[pattern])
			else:
				self._hierarchyList[pattern] = [hierarchyData[pattern]]

	@property
	def attributes(self):
		return self._attributes
	@attributes.setter
	def attributes(self, value):
		self._attributes = value
	def getAttribute(self, itemId):
		return self._attributes[itemId]
	def getAttributes(self):
		return self._attributes
	def getAttributeIndex(self, itemId):
		return self._attributes.keys().index(itemId)
	def addAttribute(self, itemId, value):
		if itemId not in self._attributes.keys():
			self._attributes[itemId] = value
			self._bdcolnames.append(value.sqlName)
			self._numberOfAttributes += 1
	def addAttributes(self, attributeList):
		for attrKey in attributeList.keys():
			if attrKey not in self._attributes.keys():
				self._attributes[attrKey] = attributeList[attrKey]
				self._bdcolnames.append(attributeList[attrKey].sqlName)
				self._numberOfAttributes += 1
	def removeAttribute(self, itemId):
		del self._attributes[itemId]
		del self._bdcolnames[self._bdcolnames.index(self._attributes[itemId].sqlName)]
		self._numberOfAttributes -= 1
	def clearAttributes(self):
		self._numberOfAttributes = 0
		self._attributes = OrderedDict()
		self._bdcolnames = list()

	@property
	def numberOfAttributes(self):
		return self._numberOfAttributes
	@numberOfAttributes.setter
	def numberOfAttributes(self, value):
		self._numberOfAttributes = value

	@property
	def tables(self):
		return self._tables
	def getTable(self, tableId):
		return self._tables[tableId]
	def addTable(self, tableId, value):
		self._tables[tableId] = value
	def removeTable(self, tableId):
		del self._tables[tableId]

	@property
	def operations(self):
		return self._operations
	def getOperations(self, level):
		return self._operations[level]
	def getOperation(self, level, opetationId):
		return self._operations[level][opetationId]
	def addOperationLevel(self, level, value):
		self._operations[level] = value
	def addOperation(self, level, opetationId, value):
		if level not in self._operations.keys():
			self._operations[level] = dict()
		if opetationId not in self._operations[level].keys():
			self._operations[level][opetationId] = list()
		if isinstance(value, list):
			for tmp in value:
				self._operations[level][opetationId].append(tmp)
		else:
			self._operations[level][opetationId].append(value)
	def addOperations(self, level, opetations):
		if level not in self._operations.keys():
			self._operations[level] = dict()
		for opetationId in opetations.keys():
			if opetationId not in self._operations[level].keys():
				self._operations[level][opetationId] = list()
			if isinstance(opetations[opetationId], list):
				for tmp in opetations[opetationId]:
					self._operations[level][opetationId].append(tmp)
			else:
				self._operations[level][opetationId].append(opetations[opetationId])
	def removeOperation(self, level, opetationId):
		del self._operations[level][opetationId]
	def setOperations(self, operations):
		self._operations = operations

	def getCountersList(self):
		countersList = list()
		for tableId in self._tables.keys():
			tableObj = self._tables[tableId]
			for counterId in tableObj.counters.keys():
				if counterId not in countersList:
					countersList.append(counterId)
		return countersList

	def update(self, attrB, value):
		logger = Logger('processLogger').get()

		attr = attrB.upper()
		if attr == 'OSSID':
			self._ossId = value
		elif attr == 'ID' or attr == 'TYPEID':
			self._typeId = value
		elif attr == 'TABLES':
			self._tables = value
		elif attr in ['MEASUREDOBJECT', 'MEASUREDOBJECTS']:
			self._measuredObject = value
		elif attr == 'ATTRIBUTES':
			self._attributes = value
		elif attr == 'NAME':
			self._name = value
		elif attr == 'TECH':
			self._tech = value
		elif attr == 'DESC':
			self._desc = value
		elif attr == 'BDCOLNAME':
			idx = self._bdcolnames.index(value[0])
			del self._bdcolnames[idx]
			self._bdcolnames.insert(idx, value[1])
		elif attr == 'BDID':
			try:
				if value[1] != value[0]:
					self._attributes = self.insert_key_value(self._attributes, value[1], value[0], self._attributes[value[0]])
					self._attributes.pop(value[0])
			except:
				logger.warning(' Something is up in attribute ID "{:s}" in unit "{:s}"'.format(value[0], self._ossId))
		elif attr == 'TABLEID':
			if value[1] != value[0]:
				self._tables = self.insert_key_value(self._tables, value[1], value[0], self._tables[value[0]])
				self._tables.pop(value[0])
		else:
			if attrB in self._extra.keys():
				self._extra[attrB].update(value)
			else:
				self._extra[attrB] = extraTag()
				self._extra[attrB].create(attrB, value)
				logger.warning('The tag "{:s}" was added to unit'.format(attrB))

	def get(self, attrB):
		logger = Logger('processLogger').get()

		attr = attrB.upper()
		if attr == 'ID':
			return self._typeId
		elif attr == 'OSSID':
			return self._ossId
		elif attr == 'UDN':
			return self._udn
		elif attr == 'SQLNAME':
			return self._sqlName
		elif attr == 'NAME':
			return self._name
		elif attr == 'DESC':
			return self._desc
		elif attr == 'TECH':
			return self._tech
		elif attr in ['MEASUREDOBJECT', 'MEASUREDOBJECTS']:
			return self._measuredObject
		else:
			if attrB in self._extra.keys():
				return self._extra[attrB]
			else:
				logger.warning('The tag "{:s}" is missing in unit {:s}'.format(attrB, self._typeId))
		return None

	def add(self, attrB, value, catalogType='*'):
		#logger = Logger('processLogger').get()

		attr = attrB.upper()
		if attr == 'ID':
			self._typeId = value
		elif attr == 'OSSID':
			self._ossId = value
		elif attr == 'UDN':
			self._udn = value
		elif attr == 'SQLNAME':
			self._sqlName = value
		elif attr == 'NAME':
			self._name = value
		elif attr == 'DESC':
			self._desc = value
		elif attr == 'TECH':
			self._tech = value
		elif attr in ['MEASUREDOBJECT', 'MEASUREDOBJECTS']:
			self._measuredObject = value
		else:
			x = extraTag()
			x.create(attrB, value, catalogType)
			self._extra[attr] = x

	def insert_key_value(self, a_dict, key, pos_key, value):
		new_dict = OrderedDict()
		for k, v in a_dict.items():
			if k == pos_key:
				new_dict[key] = value  # insert new key
			new_dict[k] = v
		return new_dict