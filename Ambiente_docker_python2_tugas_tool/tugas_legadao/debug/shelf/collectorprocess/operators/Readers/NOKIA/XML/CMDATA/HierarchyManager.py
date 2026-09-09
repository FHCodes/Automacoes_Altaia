#!/usr/bin/env python

__doc__ = \
'''
	Enrichment Operator
'''

__version__ = '0.1'

__authors__ = [
	"Version 0.1: Francisco Santiago <francisco-j-santiago@telecom.pt>",
	"Version 0.2: Gil Martins <gil-l-martins@alticelabs.com>"
			]

class HierarchyManager():

	#Class Constructor
	def __init__(self, options={}):
		self.tree = dict()
		self.requiredFields = {
								"NAME": "",
								"CLASS": ""
							}

	def getRequiredFields(self):
		return self.requiredFields

	def getTree(self):
		return self.tree

	def validateFields(self, dictToBeTested):
		"""
		Evaluates incoming dict against the requiredFields dict to check that all required ones are there
		"""
		if all(k in dictToBeTested for k in self.getRequiredFields().keys()):
			return True
		else:
			try:
				if dictToBeTested['CLASS'] == 'BTS' and 'NAME' not in dictToBeTested:
					if 'NWNAME' in dictToBeTested or 'SEGMENTNAME' in dictToBeTested:
						return True
			except KeyError:
				return False
			
			return False
		
	def addManagedObject(self, newMO):

		if not self.validateFields(newMO): return False

		tree = self.getTree()
		
		try:
			tree[newMO["DISTNAME"]] = newMO["NAME"]
		except KeyError:
			if newMO['CLASS'] == 'BTS':
				if 'SEGMENTNAME' in newMO:
					tree[newMO["DISTNAME"]] = newMO["SEGMENTNAME"]
				elif 'NWNAME' in newMO:
					tree[newMO["DISTNAME"]] = newMO["NWNAME"]
				else:
					return False
				
		return True

	def getParents(self, distName):	
		dnList = distName.split("/")
		tree = self.getTree()
		#Remove own MO from distName
		#dnList.pop()

		parents = dict()

		while dnList:
			#This direct parent
			parentName = dnList[-1].split("-")[0] + "_NAME"

			#Evaluate current distName to look for this parent
			parentDistName = "/".join(dnList)

			if parentDistName != "PLMN-PLMN":

				if parentDistName in tree:
					parents[parentName] = tree[parentDistName]

			dnList.pop()

		return parents