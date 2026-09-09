__doc__ = \
	__version__ = '1.0'
__authors__ = ['Version 0.1: Bruno Silva <bruno-e-silva@alticelabs.com>']

class hierarchy():

	def __init__(self):
		self._pattern = ''
		self._newFields = list()

	def create(self, pattern, newFields):
		self._pattern = pattern
		self._newFields = newFields

	@property
	def pattern(self):
		return self._pattern
	@pattern.setter
	def pattern(self, value):
		self._pattern = value

	@property
	def name(self):
		return self._pattern

	@property
	def newFields(self):
		return self._newFields
	def addNewField(self, itemId):
		self._newFields.append(itemId)
	def removeNewField(self, itemId):
		del self._newFields[self._newFields.index(itemId)]
