__doc__ = \
	__version__ = '1.0'
__authors__ = ['Version 0.1: Bruno Silva <bruno-e-silva@alticelabs.com>']

from lib.objects.generic.extraTag import extraTag
import abc

class baseType(object):

	def __init__(self):
		self._prev = None
		self._next = None
		self._typeId = ''
		self._name = ''
		self._udn = ''
		self._sqlName = ''
		self._desc = ''
		self._extra = dict()

	@property
	def typeId(self):
		return self._typeId
	@typeId.setter
	def typeId(self, value):
		self._typeId = value

	@property
	def extra(self):
		return self._extra
	def addExtra(self, tagId, value, catType='*'):
		if tagId not in self._extra.keys():
			self._extra[tagId] = extraTag()
			self._extra[tagId].create(tagId, value, catType)
	def getExtraCatalog(self, catType):
		outDict = dict()
		for attr in self._extra.keys():
			if self._extra[attr].catalogType.upper() == catType.upper() or self._extra[attr].catalogType == '*':
				outDict[attr] = self._extra[attr]
		return outDict

	@property
	def name(self):
		return self._name
	@name.setter
	def name(self, value):
		self._name = value

	@property
	def udn(self):
		return self._udn
	@udn.setter
	def udn(self, value):
		self._udn = value

	@property
	def sqlName(self):
		return self._sqlName
	@sqlName.setter
	def sqlName(self, value):
		self._sqlName = value

	@property
	def desc(self):
		return self._desc
	@desc.setter
	def desc(self, value):
		self._desc = value

	def get(self, attr):
		if attr == 'ID':
			return self._typeId
		elif attr == 'UDN':
			return self._udn
		elif attr == 'SQLNAME':
			return self._sqlName
		elif attr == 'NAME':
			return self._name
		elif attr == 'DESC':
			return self._desc
		elif attr in self._extra.keys():
			return self._extra[attr]
		return None