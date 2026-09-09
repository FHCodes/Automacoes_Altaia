__doc__ = \
	__version__ = '1.0'
__authors__ = ['Version 0.1: Bruno Silva <bruno-e-silva@alticelabs.com>']

import re

# #
# Removes unwanted chars from description
# #
def process(unitDict, config):

	for ossId in unitDict.keys():
		unitObj = unitDict[ossId]
		#unitObj.desc = keyWordReplacer(unitObj.desc)
		unitObj.desc = re.sub(r'\n|\r|\t', ' ', unitObj.desc)
		unitObj.desc = re.sub(r'"', '\'', unitObj.desc)
		while '  ' in unitObj.desc:
			unitObj.desc = unitObj.desc.replace('  ', ' ')
		while unitObj.desc.startswith(' '):
			unitObj.desc = unitObj.desc[1:]
		while unitObj.desc.endswith(' '):
			unitObj.desc = unitObj.desc[:-1]

		for tableId in unitObj.tables.keys():
			tableObj = unitObj.tables[tableId]
			for counterId in tableObj.counters.keys():
				counterObj = tableObj.getCounter(counterId)
				#counterObj.desc = keyWordReplacer(counterObj.desc.split('.')[0])
				counterObj.desc = counterObj.desc.strip('\n|\r| ')
				counterObj.desc = re.sub(r'"', '\'', counterObj.desc)
				counterObj.desc = re.sub(r'\<.+?\>', '', counterObj.desc)
				counterObj.desc = re.sub(r'\<|\>', '', counterObj.desc)
				while '  ' in counterObj.desc:
					counterObj.desc = counterObj.desc.replace('  ', ' ')

def keyWordReplacer(desc):
	# or r'((\\n)|(&)|(#*.[^;];))'
	if 'OLD:' in desc:
		desc = desc.split('OLD:')[0]
	return re.sub(r'((\\r)|(\\n)|(&)|(#.*?;))', '', desc)