__doc__ = \
	__version__ = '1.0'
__authors__ = ['Version 0.1: Bruno Silva <bruno-e-silva@alticelabs.com>']

from collections import OrderedDict
from lib.Logger import Logger

class hierarchyField():

	def __init__(self, myId, prevNode, myValue, famId):
		self.myId = myId
		self.famList = list()
		#if famId not in self.famList and famId != '':
		#	self.famList.append(famId)
		self.prevNode = prevNode
		self.nextNodeList = list()
		self.myValue = myValue

	def addNode(self, newId, myValue, famId):
		if newId == self.myId:
			#if famId not in self.famList and famId != '':
			#	self.famList.append(famId)
			return self
		if self.existsNextNode(newId, myValue):
			node = self.findNextNode(newId, myValue)
			#if famId not in node.famList and famId != '':
			#	node.famList.append(famId)
			return node
		nNode = hierarchyField(newId, self, myValue, famId)
		self.nextNodeList.append(nNode)
		return nNode

	def findPrevNode(self, prevNodeId):
		if self == prevNodeId:
			return self

		if self.prevNode.myId == prevNodeId:
			return self.prevNode

		return None

	def findNextNode(self, nextNodeId, nextNodeValue):
		if self == nextNodeId:
			return self

		if self.nextNodeList == []:
			return None

		for nextNode in self.nextNodeList:
			if nextNode.myId == nextNodeId and nextNodeValue == nextNode.myValue:
				return nextNode

		return None

	def existsNextNode(self, nextNodeId, nextNodeValue):
		for node in self.nextNodeList:
			if nextNodeId == node.myId and nextNodeValue == node.myValue:
				return True
		return False

	def goToFirst(self):
		node = self
		while node.prevNode != None:
			node = node.prevNode
		return node

	@property
	def myId(self):
		return self.myId
	@myId.setter
	def myId(self, value):
		self.myId = value

	@property
	def myValue(self):
		return self.myValue
	@myValue.setter
	def myValue(self, value):
		self.myValue = value

	@property
	def prevNode(self):
		return self.prevNode
	@prevNode.setter
	def prevNode(self, value):
		self.prevNode = value

	@property
	def famList(self):
		return self.famList
	@famList.setter
	def famList(self, value):
		self.famList = value
	def addFamId(self, famId):
		self.famList.append(famId)

	@property
	def nextNodeList(self):
		return self.nextNodeList
	@nextNodeList.setter
	def nextNodeList(self, value):
		self.nextNodeList = value
	def hasNextNode(self):
		return (True if len(self.nextNodeList) > 0 else False)
	def getNextListIds(self):
		nextList = list()
		for node in self.nextNodeList:
			nextList.append(node.myId)
		return nextList
	def getAllNextFam(self, node, listOfFam):
		#print listOfFam
		if not node.hasNextNode():
			return listOfFam
		for nextNode in node.nextNodeList:
			if len(nextNode.famList) > 0:
				for fm in nextNode.famList:
					if fm not in listOfFam:
						listOfFam.append(fm)
			listOfFam = self.getAllNextFam(nextNode, listOfFam)
		return listOfFam
	def getNextListTuples(self):
		nextList = list()
		for node in self.nextNodeList:
			nextList.append((node.myId, node.myValue))
		return nextList

	def getLevelRegex(self, node, config):
		if node.prevNode == None:
			return '{:s}'.format(node.myId)
		return '{:s}{:s}(.+?){:s}(.*){:s}'.format(self.getLevelRegex(node.prevNode, config), config['sepCharPattern'], config['interChar'], node.myId)

	def printData2(self):
		fNode = self.goToFirst()
		print('{:s}|{:s}|{:s}|{:s}'.format('Parend Id', 'Hierachy Level Id', 'Value', 'In Level'))
		print('{:s}|{:s}|{:s}|{:s}'.format('', fNode.myId, fNode.myValue, fNode.famList))
		spacer = '{:s}'.format('|')
		for node in fNode.nextNodeList:
			print('{:s}{:s}|{:s}|{:s}|{:s}'.format(spacer, node.prevNode.myId, node.myId, node.myValue, node.famList))
			if node.nextNodeList != []:
				self.continuePrinting(node, spacer)

	def printData(self):
		fNode = self.goToFirst()
		print('{:s}|{:s}|{:s}'.format('Hierachy Level Id', 'Value', 'In Level'))
		print('{:s}|{:s}|{:s}'.format('', fNode.myId, fNode.myValue, fNode.famList))
		spacer = '{:s}'.format('|')
		for node in fNode.nextNodeList:
			print('{:s}{:s}|{:s}|{:s}'.format(spacer, node.myId, node.myValue, node.famList))
			if node.nextNodeList != []:
				self.continuePrinting(node, spacer)


	def continuePrinting(self, fNode, spacer):
		spacer += '{:s}'.format('|')
		for node in fNode.nextNodeList:
			print('{:s}{:s}|{:s}|{:s}'.format(spacer, node.myId, node.myValue, node.famList))
			self.continuePrinting(node, spacer)

	def getDeps(self, node, unitSplitList, config):
		print config['sepCharPattern']
		if len(node.nextNodeList) > 1:
			for nextNode in node.nextNodeList:
				levelRegex = '{:s}{:s}{:s}{:s}.*$'.format(nextNode.getLevelRegex(nextNode, config), config['sepCharPattern'], nextNode.myValue, '' if nextNode.myValue == '' else config['interChar'])
				if levelRegex not in unitSplitList.keys():
					unitSplitList[levelRegex] = dict()
					unitSplitList[levelRegex]['level'] = nextNode.myId
					unitSplitList[levelRegex]['value'] = nextNode.myValue
					unitSplitList[levelRegex]['familyList'] = nextNode.getAllNextFam(nextNode, list())
					continue
				unitSplitList[levelRegex]['familyList'] = nextNode.getAllNextFam(nextNode, unitSplitList[levelRegex]['familyList'])
				unitSplitList.update(self.getDeps(nextNode, unitSplitList, config))
			return unitSplitList
		try:
			unitSplitList.update(self.getDeps(node.nextNodeList[0], unitSplitList, config))
		except:
			pass
		return unitSplitList