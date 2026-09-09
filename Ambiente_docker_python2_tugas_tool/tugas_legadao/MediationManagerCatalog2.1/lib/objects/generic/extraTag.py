__doc__ = \
	__version__ = '1.0'
__authors__ = ['Version 0.1: Bruno Silva <bruno-e-silva@alticelabs.com>']

import abc

class extraTag(object):

	def __init__(self):
		self._tag = ''
		self._value = ''
		self._catalogType = '*'

	def create(self, tag, value, catalogType='*'):
		self._tag = tag
		self._value = value
		self._catalogType = catalogType

	def update(self, extraObj):
		self._value = extraObj.value
		self._catalogType = extraObj.catalogType

	@property
	def tag(self):
		return self._tag
	@tag.setter
	def tag(self, value):
		self._tag = value

	@property
	def value(self):
		return self._value
	@value.setter
	def value(self, data):
		self._value = data

	@property
	def catalogType(self):
		return self._catalogType
	@catalogType.setter
	def catalogType(self, value):
		self._catalogType = value

	def update(self, value):
		self._value = value
