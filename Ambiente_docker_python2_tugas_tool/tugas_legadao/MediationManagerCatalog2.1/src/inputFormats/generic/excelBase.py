__doc__ = \
	__version__ = '1.0'
__authors__ = ['Version 0.1: Bruno Silva <bruno-e-silva@alticelabs.com>']

import abc
import xlrd
from lib.functions import *
from lib.Logger import Logger

# #
# The base code for reading microsoft excel files (.xls or .xlsx)
# #
class excelBase():

	def __init__(self,docPath,fileConfig,catalogType):
		self.logger = Logger('processLogger').get()
		self.docPath = docPath
		self.catalogType = catalogType
		self.fileConfig = fileConfig

	# #
	# This function struct must be implemented in the inputFormats created
	# #
	@abc.abstractmethod
	def process(self, docPath, fileConfigName, catalogType, vendor):
		print '[WARNING]: function process() is not defined'

	# #
	# Gets the data in the path passed and with the input configuration, reads the data in the excel
	# And validates that the "must have" fields are created
	# #
	def getExcelInfo(self, info=dict()):
		workBook = xlrd.open_workbook(self.docPath)
		self.logger.debug("  * Reading data from file {:38s} *".format(self.docPath))

		for key in sorted(self.fileConfig.keys()):
			self.logger.debug("  ********** {:39s}{:4s} **********".format('Starting To Process inputConfigs: ', str(key)))
			sheet = self.fileConfig[key]['sheetName']
			info = self.getSheetData(workBook.sheet_by_name(sheet), self.fileConfig[key], info)
			self.logger.success("* Finishing Processing inputConfigs {:28s}*".format(str(key)))

		# Validates the "must have" fields
		attrUnit = ['id', 'ossId', 'name', 'udn', 'desc', 'tableName', 'hierarchy']
		attrItem = ['id', 'bdcolname', 'name', 'udn', 'desc', 'bdtype', 'dataType', 'dataUnit']
		unitPos = 0

		while unitPos < len(info.keys()):
			unitId = info.keys()[unitPos]
			if 'desc' in info[unitId]['attributes']:
				info[unitId]['attributes']['desc'] = re.sub(r'"', '\'', info[unitId]['attributes']['desc'])

			if not set(attrUnit).issubset(info[unitId]['attributes'].keys()):
				self.logger.error("  * {:s}{:s} *".format('Missing attributes in unit ', unitId))
				del info[unitId]
				continue
			else:
				itemPos = 0
				while itemPos < len(info[unitId]['items'].keys()):
					itemId = info[unitId]['items'].keys()[itemPos]
					if 'desc' in info[unitId]['items'][itemId]:
						info[unitId]['items'][itemId]['desc'] = re.sub(r'"', '\'', info[unitId]['items'][itemId]['desc'])
					if not set(attrItem).issubset(info[unitId]['items'][itemId].keys()):
						self.logger.error("  * {:s}{:s}{:s}{:s}. Missing attributes:{:s} *".format('Missing attributes in item ', itemId, ' from unit ', unitId, str(list(set(attrItem)-set(info[unitId]['items'][itemId].keys()))).encode('utf-8')))
						del info[unitId]['items'][itemId]
						continue
					itemPos += 1
			unitPos += 1
		return info

	# #
	# Gets the positions of the columns in the configuration file on the sheet passed
	# #
	def getColumnsIndex(self, sheet, typeConfig):

		fieldMatch = typeConfig['fieldMatch']
		for key in fieldMatch.keys():
			flag = True
			for position in range(0, sheet.ncols):
				if sheet.cell(0, position).value == fieldMatch[key]:
					fieldMatch[key] = position
					flag = False
					break
			if flag:
				fieldMatch[key] = -1
		return typeConfig

	# #
	# With base in the type of date gets the sheed data
	# #
	def getSheetData(self, sheet, typeConfig, info):
		if 'unit' in typeConfig:
			info = self.getUnitData(sheet, self.getColumnsIndex(sheet, typeConfig['unit']), info)
		if 'item' in typeConfig:
			info = self.getItemData(sheet, self.getColumnsIndex(sheet, typeConfig['item']), info)
		return info

	# #
	# To process the data in sheed for unit
	# #f
	def getUnitData(self, sheet, typeConfig, info):
		appendList = ['hierarchy']
		fieldMatch = typeConfig['fieldMatch']
		unitType = typeConfig['unitId']
		try:
			startLine = (1 if self.tryConvert(sheet.cell(0, 0).value).upper() != self.tryConvert(
				sheet.cell(1, 0).value).upper() and self.tryConvert(sheet.cell(1, 0).value).upper() != '' else 2)
			for row in range(startLine, sheet.nrows):
				try:
					typeId = self.tryConvert(sheet.cell(row, fieldMatch[unitType]).value).upper()
				except:
					return

				onlyAppend = False
				if typeId not in info:
					info[typeId] = dict()
					info[typeId]['attributes'] = dict()
					info[typeId]['attributes']['disableHierarchy'] = "False"
					info[typeId]['items'] = dict()
				else:
					onlyAppend = True
				for tag in fieldMatch:
					if tag in info[typeId]['attributes']:
						if info[typeId]['attributes'][tag] == '':
							if fieldMatch[tag] != -1:
								info[typeId]['attributes'][tag] = self.tryConvert(
									sheet.cell(row, fieldMatch[tag]).value)
							continue
					# if reaches here, tag doesn't exist, or if it exists is != ""
					if onlyAppend:
						# if tag is hierarchy (only one in appendList thus far)
						if tag in appendList:
							if fieldMatch[tag] != -1:
								try:
									# tag exists and is != "", new fieldMatch[tag] != -1, so it appends
									info[typeId]['attributes'][tag] += ',' + self.tryConvert(
										sheet.cell(row, fieldMatch[tag]).value)
								except KeyError:
									# tag doesn't exist yet, despite the family already existing in 'info', and fieldMatch[tag] != -1
									info[typeId]['attributes'][tag] = self.tryConvert(
										sheet.cell(row, fieldMatch[tag]).value)
							elif tag not in info[typeId]['attributes']:
								# tag doesn't exist yet, despite the family already existing in 'info', but fieldMatch[tag] == -1
								self.logger.warning(
									"  * {:s}{:s} *".format('Possibly missing hierarchy in unit ', typeId))
								info[typeId]['attributes'][tag] = ''
							continue
					# other cases: tag doesn't exist yet, or if it does, it's not in appendList (hierarchy)
					# each passage overwrites previous if it reaches here
					if fieldMatch[tag] != -1:
						info[typeId]['attributes'][tag] = self.tryConvert(sheet.cell(row, fieldMatch[tag]).value)
					else:
						info[typeId]['attributes'][tag] = ''
			return info
		except:
			self.logger.error("The sheet '{0}' dont have data ".format(sheet.name))
			print ("[ERROR]: The sheet '{0}' dont have data ".format(sheet.name))
			return info


	# #
	# To process the data in sheed for item
	# #
	def getItemData(self, sheet, typeConfig, info):
		fieldMatch = typeConfig['fieldMatch']
		unitType = typeConfig['unitId']
		itemType = typeConfig['itemId']

		for row in range(1, sheet.nrows):
			unitTypeId = self.tryConvert(sheet.cell(row, fieldMatch[unitType]).value).upper()
			typeId = self.tryConvert(sheet.cell(row, fieldMatch[itemType]).value).upper()

			if ',' in unitTypeId:
				unitList = unitTypeId.replace(' ', '').split(',')
				for unitTypeId in unitList:
					if unitTypeId in info.keys():
						if typeId not in info[unitTypeId]['items']:
							info[unitTypeId]['items'][typeId] = dict()
						for tag in fieldMatch:
							info[unitTypeId]['items'][typeId][tag] = self.tryConvert(sheet.cell(row, fieldMatch[tag]).value)
					else:
						self.logger.warning("*   MO id from Item sheet wasn\'t found on MO sheet {:12s} *".format(''))
			else:
				if unitTypeId in info.keys():
					if typeId not in info[unitTypeId]['items']:
						info[unitTypeId]['items'][typeId] = dict()
					for tag in fieldMatch:
						if fieldMatch[tag] != -1:
							try:
								info[unitTypeId]['items'][typeId][tag] = self.tryConvert(sheet.cell(row, fieldMatch[tag]).value)
							except:
								info[unitTypeId]['items'][typeId][tag] = int(self.tryConvert(sheet.cell(row, fieldMatch[tag]).value))
						else:
							info[unitTypeId]['items'][typeId][tag] = ''
				else:
					self.logger.warning("*   MO id from Item sheet wasn\'t found on MO sheet {:12s} *".format(''))
		return info

	# #
	# Gets the all the column in the data file in the cell from the sheet and in the position row, with base the config
	# #
	def getCellData(self, sheet, row, config, data, typeId, flag):

		if typeId not in data.keys():
			tmp = dict()
			for key in config.keys():
				tmp[key] = self.tryConvert(sheet.cell(row, config[key]).value)

			if flag:
				data[typeId] = list()
				data[typeId].append(tmp)
			else:
				data[typeId] = tmp
		elif flag:
			tmp = dict()
			for key in config.keys():
				tmp[key] = self.tryConvert(sheet.cell(row, config[key]).value)
			data[typeId].append(tmp)
		else:
			for key in config.keys():
				tmp = self.tryConvert(sheet.cell(row, config[key]).value)
				if tmp != data[typeId][key]:
					data[typeId][key] += ';' + tmp

	# #
	# Converts cell data to utf-8 format and removes not accepted
	# #
	def tryConvert(self, value):
		try:
			value = str(value).encode("utf-8")
		except:
			pass

		#if re.search(r'^\d.+?(\.0)', value) is not None:
		#	return value.split('.')[0]

		return re.sub(r'(^ )|\<|\>|( $)|\.0', '', value)
