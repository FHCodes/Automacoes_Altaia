__doc__ = \
__version__ = '1.0'
__authors__ = ['Version 0.1: Bruno Silva <bruno-e-silva@alticelabs.com>']

from lib.objects.column import column
import re

# NOT DONE

def process(unitData, config):
	return
	unitDict = dict()

	if unitData is not None:

		if unitData.measuredObject != '':
			unitDict[unitData.typeId] = unitData.measuredObject

		while unitData.getNext() is not None:
			unitData = unitData.getNext()

			if unitData.measuredObject != '':
				unitDict[unitData.typeId] = unitData.measuredObject

		while unitData is not None:
			if '_' in unitData.typeId:
				data = re.search(r'_([^_]+?)$', unitData.typeId)
				if data is not None:
					son = data.group(2)[1:]
					#if father in unitDict.keys():



			unitData = unitData.getPrev()



	lista2 = list()
	while prev is not None:
		lista2.append(prev.typeId)
		prev = prev.getNext()
	return

	prev = unitData
	unitList = dict()
	while unitData is not None:
		if unitData.measuredObject != '':
			unitList[unitData.typeId] = None
			pItem = None
			hier = unitData.hierarchyList
			while hier is not None:
				fieldList = list()
				newField = hier.newFields
				while newField is not None:
					if newField.typeId not in fieldList:
						nItem = item()
						nItem.create(newField.typeId, newField.name, newField.udn, newField.sqlName, newField.desc, newField.dbn0type, newField.bdtype, newField.typeCust, newField.typeVendor, newField.unitVendor, newField.multiplicity)
						if unitList[unitData.typeId] is None:
							unitList[unitData.typeId] = nItem
						else:
							nItem.setPrev(pItem)
							pItem.setNext(nItem)
						pItem = nItem
					newField = newField.getNext()
				hier = hier.getNext()
		unitData = unitData.getNext()

	while prev is not None:
		if '_' in prev.typeId:
			isFather = prev.typeId.split('_')[0]
			if isFather in unitList:
				if unitList[isFather] is not None:
					tmp = copy.copy(unitList[isFather])
					preset = prev.presetItems
					if preset is None:
						prev.presetItems = tmp
					else:
						ppreset = preset
						while ppreset is not None:
							preset = ppreset
							ppreset = ppreset.getNext()
						preset.setNext(tmp)
						tmp.setPrev(preset)
		prev = prev.getNext()
