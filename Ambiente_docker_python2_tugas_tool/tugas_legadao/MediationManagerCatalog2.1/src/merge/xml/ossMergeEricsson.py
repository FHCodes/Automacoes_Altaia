__doc__ = \
	__version__ = '1.0'
__authors__ = ['Version 0.1: Bruno Silva <bruno-e-silva@alticelabs.com>']

import xml.etree.ElementTree as ET
from lib.functions import xmlReader, writeStringToXML, writeToFile, writeToXML
from lib.Logger import Logger

# #
# Merges two XML oss catalogs into one, being the baseCatalogPath the base for the output
# #
def process(vendor, baseCatalogPath, newCatalogPath, numenclature, config):
	logger = Logger('ossMerge').get()

	baseCatalog = xmlReader(baseCatalogPath.replace('#', 'oss'))
	newCatalog = xmlReader(newCatalogPath.replace('#', 'oss'))

	logger.debug('##################################### OSS Merging Info ############################################')
	logger.debug('## Vendor: {:38s}   tech: {:38s} ##'.format(vendor, baseCatalog.find('unit').get('tech')))
	logger.debug('## Base: {:40s}   New: {:39s} ##'.format(baseCatalog.get('ossversion'),newCatalog.get('ossversion')))
	logger.debug('## Output File: {:80} ##'.format(numenclature.replace('#', 'oss')))
	logger.debug('##################################### Start OSS Merging ###########################################')

	data = dict()
	comment = list()
	baseCatalog.attrib['ossversion'] = str(baseCatalog.get('ossversion')) + '/' + str(newCatalog.get('ossversion'))

	for unit in baseCatalog.findall('unit'):
		try:
			ossId = unit.get('ossId')
			if ossId is None:
				if ET.tostring(unit.upper()) not in comment:
					comment.append(ET.tostring(unit.upper()))
			else:
				ossId = ossId.upper()
				if not ossId in data.keys():
					data[ossId] = dict()
					data[ossId]['unit'] = unit
					data[ossId]['item'] = dict()
					data[ossId]['comment'] = list()
					for item in unit:
						itemId = item.get('id')
						if itemId == None:
							if not ET.tostring(item).upper() in data[ossId]['item']:
								data[ossId]['comment'].append(ET.tostring(item).upper())
						elif not itemId.upper() in data[ossId]:
								data[ossId]['item'][itemId.upper()] = item
						else:
							logger.warning('  * [Item] Duplicated Item \"{:2s}\" in Unit with ossId: \"{:2s}\" * '.format(itemId, ossId))
				else:
					logger.warning('  * [Unit] Duplicated Unit with ossId: \"{:2s}\".'.format(ossId))
		except:
			pass

	for newUnit in newCatalog.findall('unit'):
		try:
			newUnitId = newUnit.get('ossId')
			# Verify if is comment
			if newUnitId is None:
				# Verify if comment exists in base Catalog
				if ET.tostring(newUnit.upper()) not in comment:
					baseCatalog.append(newUnit)
			# Verify if newUnit is really new, if not compares it self with existing unit
			else:
				# Gets base Unit
				newUnitId = newUnitId.upper()
				if newUnitId in data:
					unit = data[newUnitId]['unit']

					# Updates measuredobjects if, in the mergeConfiguration, the field is true
					for attr in config['unit'].keys():
						try:
							if 'measuredobjects' == attr:
								if config['unit']['measuredobjects'] == 'True':
									if unit.get('measuredobjects') != newUnit.get('measuredobjects'):
										existing = unit.get('measuredobjects').replace(' ', '').split(',')
										for key in newUnit.get('measuredobjects').replace(' ', '').split(','):
											if key not in existing:
												existing.append(key)
												unit.set('measuredobjects', unit.get('measuredobjects')+', '+key)
							elif config['unit'][attr] == 'True':
								unit.set(attr, newUnit.get(attr))
						except Exception as ex:
							print ex


					for newItem in newUnit:
						newItemId = newItem.get('id')
						# Verify if the item is a comment or not
						if newItemId == None:
							if not ET.tostring(newItem).upper() in data[newUnitId]['comment']:
								unit.append(newItem)
							elif not (ET.tostring(newItem).split(' id="')[1].split('"')[0]).upper() in data[newUnitId]['comment']:
								unit.append(newItem)
						else:
							newItemId = newItemId.upper()
							if newItemId not in data[newUnitId]['item'].keys():
								unit.append(newItem)
								data[newUnitId]['item'][newItemId] = newItem
							else:
								for attribute in config['item'].keys():
									if config['item'][attribute] == 'True':
										if attribute == 'v':
											try:
												baseVersion = data[newUnitId]['item'][newItemId].get('v').split('/')[0]
												if newItem.get('v') != data[newUnitId]['item'][newItemId].get('v'):
													data[newUnitId]['item'][newItemId].set('v', baseVersion + '/' + newItem.get('v').split('/')[1])
											except:
												data[newUnitId]['item'][newItemId].set('v', baseCatalog.get('ossversion').split('/')[0] + '/' + newItem.get('v').split('/')[1])
										elif attribute == 'typeCust':
											if newItem.get(attribute) == 'STRING' and data[newUnitId]['item'][newItemId].get(attribute) == 'INTEGER':
												continue
											elif data[newUnitId]['item'][newItemId].get(attribute) != 'TIMESTAMP':
												data[newUnitId]['item'][newItemId].set(attribute, newItem.get(attribute))
										else:
											data[newUnitId]['item'][newItemId].set(attribute, newItem.get(attribute))

				# If is new Unit, appends do base Catalog
				else:
					baseCatalog.append(newUnit)
		except:
			pass

	#writeToXML(numenclature.replace('#', 'oss'), ET.ElementTree(baseCatalog))
	writeStringToXML(numenclature.replace('#', 'oss'), baseCatalog)
	logger.debug('###################################### End OSS Merging ############################################')
