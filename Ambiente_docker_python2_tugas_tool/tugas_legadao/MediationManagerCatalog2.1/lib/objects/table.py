__doc__ = \
__version__ = '1.0'
__authors__ = ['Version 0.1: Bruno Silva <bruno-e-silva@alticelabs.com>']

from lib.objects.generic.baseType import baseType
import abc
from lib.Logger import Logger
from lib.objects.generic.extraTag import extraTag

class table(baseType):

	def __init__(self):
		baseType.__init__(self)
		self._ossId = ''
		self._counters = dict()
		self._bdcolnames = list()
		self._numberOfCounters = 0

		self._active = 'TRUE'
		self._pdfOnly = ''
		self._partitionOf = ''
		self._isStruct = False
		self._isDummy = False
		self._structDependencies = list()
		self._tech = ''

	def create(self, tableId, ossId, tableName, udn):
		self._typeId = tableId
		self._ossId = ossId
		self._udn = udn
		self._sqlName = tableName.upper()

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

	@property
	def counters(self):
		return self._counters
	def getCounterIndex(self, counterId):
		return self._counters.keys().index(counterId)
	def addCounter(self, counterId, value):
		if counterId not in self._counters.keys():
			self._counters[counterId] = value
			self._bdcolnames.append(value.sqlName)
			self._numberOfCounters += 1
	def removeCounter(self, counterId):
		del self._bdcolnames[self._bdcolnames.index(self._counters[counterId].sqlName)]
		del self._counters[counterId]
		self._numberOfCounters -= 1
	def getCounter(self, counterId):
		return self._counters[counterId]

	@property
	def active(self):
		return self._active
	@active.setter
	def active(self, value):
		self._active = value

	@property
	def tech(self):
		return self._tech
	@tech.setter
	def tech(self, value):
		self._tech = value

	@property
	def numberOfCounters(self):
		return self._numberOfCounters
	@numberOfCounters.setter
	def numberOfCounters(self, value):
		self._numberOfCounters = value

	@property
	def pdfOnly(self):
		return self._pdfOnly
	@pdfOnly.setter
	def pdfOnly(self, value):
		self._pdfOnly = value

	@property
	def partitionOf(self):
		return self._partitionOf
	@partitionOf.setter
	def partitionOf(self, value):
		self._partitionOf = value

	@property
	def hasColumns(self):
		if len(self._counters.keys()) > 0:
			return True
		return False

	@property
	def isStruct(self):
		return self._isStruct
	@isStruct.setter
	def isStruct(self, value):
		self._isStruct = value

	@property
	def structDependencies(self):
		return self._structDependencies
	@structDependencies.setter
	def structDependencies(self, value):
		self._structDependencies = value
	def addStructDependencie(self, value):
		self._structDependencies.append(value)

	def update(self, attrB, value):
		logger = Logger('processLogger').get()

		attr = attrB.upper()
		if attr == 'UDN':
			self._udn = value
		elif attr == 'TABLENAME':
			self._sqlName = value.upper()
		elif attr == 'ID':
			self._typeId = value
		elif attr == 'OSSID':
			self._ossId = value
		elif attr == 'ACTIVE':
			self._active = value
		elif attr == 'TECH':
			self._tech = value
		elif attr == 'PARTITIONOF':
			self._partitionOf = value
		elif attr == 'PDFONLY':
			self._pdfOnly = value
		elif attr == 'BDCOLNAME':
			del self._bdcolnames[self._bdcolnames.index(value[0].upper())]
			self._bdcolnames.append(value[1])
			self._counters[value[0]].update('SQLNAME', value[1])
		else:
			if attrB in self._extra.keys():
				self._extra[attrB].update(value)
			else:
				self._extra[attrB] = extraTag()
				self._extra[attrB].create(attrB, value)
				logger.warning('The tag "{:s}" was added to table {:s}'.format(attrB, self._typeId))

	def get(self, attrB):
		logger = Logger('processLogger').get()

		attr = attrB.upper()
		if attr == 'ID':
			return self._typeId
		elif attr == 'UDN':
			return self._udn
		elif attr == 'SQLNAME':
			return self._sqlName
		elif attr == 'ACTIVE':
			return self._active
		elif attr == 'TECH':
			return self._tech
		elif attr == 'OSSID':
			return self._ossId
		elif attr == 'PARTITIONOF':
			return self._partitionOf
		elif attr == 'PDFONLY':
			return self._pdfOnly
		else:
			if attrB in self._extra.keys():
				return self._extra[attrB]
			else:
				logger.warning('The tag "{:s}" is missing in table {:s}'.format(attrB, self._typeId))
		return None

	def add(self, attrB, value, catalogType='*'):
		logger = Logger('processLogger').get()

		attr = attrB.upper()
		if attr == 'UDN':
			self._udn = value
		elif attr == 'TABLENAME':
			self._sqlName = value
		elif attr == 'ID':
			self._typeId = value
		elif attr == 'OSSID':
			self._ossId = value
		elif attr == 'ACTIVE':
			self._active = value
		elif attr == 'TECH':
			self._tech = value
		elif attr == 'PARTITIONOF':
			self._partitionOf = value
		elif attr == 'PDFONLY':
			self._pdfOnly = value
		else:
			x = extraTag()
			x.create(attrB, value, catalogType)
			self._extra[attrB] = x
