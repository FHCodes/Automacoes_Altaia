__doc__ = \
	__version__ = '1.0'
__authors__ = ['Version 0.1: Bruno Silva <bruno-e-silva@alticelabs.com>']

from xml.etree import ElementTree

class myTreeBuilder(ElementTree.TreeBuilder):

	# #
	# Enables reading comments
	# #
   def comment(self, data):
       self.start(ElementTree.Comment, {})
       self.data(data)
       self.end(ElementTree.Comment)
