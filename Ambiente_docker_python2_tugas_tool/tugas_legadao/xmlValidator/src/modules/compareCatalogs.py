# from Validator.lib.Logger import Logger
from lib.Logger import Logger
from collections import OrderedDict


class compareCatalogs():
	def __init__(self, client, oss, operations, logname):
		self.client = client
		self.oss = oss
		self.operations = operations
		self.logger = Logger(logname).get()

	def compareClOss(self):
		error = False
		dictClient = dict()
		dictOss = dict()
		idsOss = []
		idsClient = []

		self.logger.debug("********** COMPARE CLIENT AND OSS CATALOGS **********")
		for table in self.client['root']['table']:
			ossID = table['ossId'].upper()
			if ossID not in dictClient:
				dictClient[ossID] = []
			idsClient.append(ossID)

			try:
				for column in table['column']:
					dictClient[ossID].append(column['id'].upper())
			except:
				pass
		for unit in self.oss['root']['unit']:
			ossID = unit['ossId'].upper()
			dictOss[ossID] = []
			idsOss.append(ossID)

			try:
				for item in unit['item']:
					dictOss[ossID].append(item['id'].upper())
			except:
				pass

		comparison = list(set(idsOss) - set(idsClient))
		if comparison:
			self.logger.error("<OSS ID> not found in Client Catalog: " + str(comparison))
			error = True

		comparison = list(set(idsClient) - set(idsOss))
		if comparison:
			self.logger.error("<OSS ID> not found in OSS Catalog: " + str(comparison))
			error = True

		keys = list(set(dictClient.keys() + dictOss.keys()))

		for id in keys:
			try:
				comparison = list(set(dictOss[id]) - set(dictClient[id]))
				if comparison:
					self.logger.error("[" + id + "] <Column ID> not found in Client Catalog: " + str(comparison))
					error = True
			except Exception:
				pass

			try:
				comparison = list(set(dictClient[id]) - set(dictOss[id]))
				if comparison:
					self.logger.error("[" + id + "] <Item ID> not found in OSS Catalog: " + str(comparison))
					error = True
			except Exception:
				pass
			
		# TECH MATCHING VALIDATION
		tech = {}
		for table in self.client['root']['table']:  # save all client tables 'tech'
			oss_id = table['ossId'].upper()
			try:
				if oss_id not in tech.keys():
					tech[oss_id] = table['tech']
			except KeyError:
				error = True
				self.logger.error("[" + oss_id + "] Attribute 'tech': Missing in Client Catalog")
				
		for unit in self.oss['root']['unit']:  # compare with oss units 'tech'
			oss_id = unit['ossId'].upper()
			if oss_id in tech.keys():
				try:
					if unit['tech'] != tech[oss_id]:
						error = True
						self.logger.error(
							"[" + oss_id + "] Attribute 'tech': Mismatch between Client and OSS Catalogs - Client: {0} | OSS: {1}".format(tech[oss_id], unit['tech']))
				except KeyError:
					error = True
					self.logger.error("[" + oss_id + "] Attribute 'tech': Missing in OSS Catalog")
		
		if not error:
			# self.logger.info("Success in comparison between Client and Oss")
			self.logger.success("Success in comparison between Client and Oss")


	def compareClOp(self):
		error = False
		idsClient = []
		idsOperations = []
		exclude = []

		self.logger.debug("********** COMPARE CLIENT AND OPERATIONS CATALOGS **********")
		for table in self.client['root']['table']:
			tableid = table['id'].upper()
			idsClient.append(tableid)

		if 'unit' in self.operations['root']:
			for unit in self.operations['root']['unit']:
				if "operation" in unit:
					if type(unit["operation"]) == OrderedDict:
						if unit["operation"]["type"] == 'unitSplitv2':
							exclude.append(unit["id"].upper())
					else:
						for operation in unit["operation"]:
							if operation["type"] == 'unitSplitv2':
								exclude.append(unit["id"].upper())

				idop = unit['id'].upper()
				idsOperations.append(idop)

		idsOperations = list(set(idsOperations) - set(exclude))
		comparison = list(set(idsOperations) - set(idsClient))
		if comparison:
			self.logger.error("<ID> not found in Client Catalog: " + str(comparison))
			error = True

		if not error:
			# self.logger.info("Success in comparison between Client and Operation")
			self.logger.success("Success in comparison between Client and Operation")
