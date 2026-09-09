__doc__ = \
__version__ = '1.0'
__authors__ = ['Version 0.1: Bruno Silva <bruno-e-silva@alticelabs.com>']

from lib.objects.generic.baseType import baseType
from lib.Logger import Logger
from lib.objects.generic.extraTag import extraTag

class column(baseType):

	def create(self, itemId, name, udn, sqlName, desc, dbn0type, bdtype, typeCust, typeVendor, unitVendor, multiplicity, version=''):
		self._typeId = itemId
		self._name = name
		self._udn = udn
		self._sqlName = sqlName.upper()
		self._desc = desc
		self._dbn0type = dbn0type
		self._bdtype = bdtype
		self._typeCust = typeCust
		self._typeVendor = typeVendor
		self._unitVendor = unitVendor
		#Preset compressed field to False
		self._compressed = 'False'
		self._multiplicity = multiplicity
		self._version = version

	@property
	def dbn0type(self):
		return self._dbn0type
	@dbn0type.setter
	def dbn0type(self, value):
		self._dbn0type = value

	@property
	def version(self):
		return self._version
	@version.setter
	def version(self, value):
		self._version = value

	@property
	def bdtype(self):
		return self._bdtype
	@bdtype.setter
	def bdtype(self, value):
		self._bdtype = value

	@property
	def typeCust(self):
		return self._typeCust
	@typeCust.setter
	def typeCust(self, value):
		self._typeCust = value

	@property
	def typeVendor(self):
		return self._typeVendor
	@typeVendor.setter
	def typeVendor(self, value):
		self._typeVendor = value

	@property
	def unitVendor(self):
		return self._unitVendor
	@unitVendor.setter
	def unitVendor(self, value):
		self._unitVendor = value

	@property
	def compressed(self):
		return self._compressed
	@compressed.setter
	def compressed(self, value):
		self._compressed = value

	@property
	def multiplicity(self):
		return self._multiplicity
	@multiplicity.setter
	def multiplicity(self, value):
		self._multiplicity = value

	def update(self, attrB, value):
		logger = Logger('processLogger').get()

		attr = attrB.upper()
		if attr == 'UDN':
			self._udn = value
		elif attr == 'BDCOLNAME':
			self._sqlName = value.upper()
		elif attr == 'SQLNAME':
			self._sqlName = value.upper()
		elif attr == 'ID':
			self._typeId = value
		elif attr == 'DESC':
			self._desc = value
		elif attr == 'TYPECUST':
			self._typeCust = value
		elif attr == 'TYPEVENDOR':
			self._typeVendor = value
		elif attr == 'UNITVENDOR':
			self._unitVendor = value
		elif attr == 'NAME':
			self._name = value
		elif attr == 'BDTYPE':
			self._bdtype = value
		elif attr == 'DBN0TYPE':
			self._dbn0type = value
		elif attr in ['VERSION', 'V']:
			if self._version == '':
				self._version = value
			elif value == '':
				return
			else:
				self._version = (self._version.split('/')[0] if '/' in self._version else self._version) + '/' + (value.split('/')[1] if '/' in value else value)
		else:
			if attrB in self._extra.keys():
				self._extra[attrB].update(value)
			else:
				self._extra[attrB] = extraTag()
				self._extra[attrB].create(attr, value)
				logger.warning('The tag "{:s}" was added to column {:s}'.format(attrB, self._typeId))

	def get(self, attrB):
		logger = Logger('processLogger').get()

		attr = attrB.upper()
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
		elif attr == 'UNITVENDOR':
			return self._unitVendor
		elif attr == 'TYPEVENDOR':
			return self._typeVendor
		elif attr == 'TYPECUST':
			return self._typeCust
		elif attr == 'DBN0TYPE':
			return self._dbn0type
		elif attr == 'BDTYPE':
			return self._bdtype
		elif attr in ['VERSION', 'V']:
			return self._version
		else:
			if attrB in self._extra.keys():
				return self._extra[attrB]
			else:
				logger.warning('The tag "{:s}" is missing in column {:s}'.format(attrB, self._typeId))
		return None

	def add(self, attrB, value, catalogType='*'):
		#logger = Logger('processLogger').get()

		attr = attrB.upper()
		if attr == 'ID':
			self._typeId = value
		elif attr == 'UDN':
			self._udn = value
		elif attr == 'SQLNAME':
			self._sqlName = value
		elif attr == 'NAME':
			self._name = value
		elif attr == 'DESC':
			self._desc = value
		elif attr == 'UNITVENDOR':
			self._unitVendor = value
		elif attr == 'TYPEVENDOR':
			self._typeVendor = value
		elif attr == 'TYPECUST':
			self._typeCust = value
		elif attr == 'DBN0TYPE':
			self._dbn0type = value
		elif attr == 'BDTYPE':
			self._bdtype = value
		elif attr in ['VERSION', 'V']:
			self._version = value
		else:
			x = extraTag()
			x.create(attrB, value, catalogType)
			self._extra[attrB] = x
