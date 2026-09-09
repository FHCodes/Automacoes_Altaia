__doc__ = \
	__version__ = '1.0'
__authors__ = [
	'Version 0.1: Gil Martins <gil-l-martins@alticelabs.com>'
]

from lib.functions import validateSqlName

# #
# Overrides attribute value for a given field - ex: bdtype from default VARCHAR2(256) to VARCHAR2(3000)
'''
"setAttribute": [
	{
		"id": "RESERVEDBY",
		"attribute": "bdtype",
		"value": "VARCHAR2(3000)"
	},
	{
		"id": "PUBLICKEY",
		"attribute": "bdtype",
		"value": "VARCHAR2(3000)",
		"units": ["SERVERKEY", "OTHER"]
	}
]
'''
# #


def process(unitDict, config):
	for ossId in unitDict.keys():
		unit_obj = unitDict[ossId]
		
		try:
			# check for 'units' in config to filter units to apply
			all_units = True
			if 'units' in config and isinstance(config['units'], list):
				all_units = False
				config['units'] = [str(x).upper() for x in config['units']]
			
			if not all_units:
				if ossId.upper() not in config['units']:
					continue
			
			# apply attribute change if field exists
			changed = False
			for counter_id in unit_obj.attributes.keys():
				if config['id'].upper() == counter_id.upper():
					changed = True
					counter_obj = unit_obj.attributes[counter_id]
					setattr(counter_obj, config['attribute'], config['value'])
					break
			
			if not changed:
				for table_id in unit_obj.tables:
					table_obj = unit_obj.tables[table_id]
					
					for counter_id in table_obj.counters.keys():
						if config['id'].upper() == counter_id.upper():
							counter_obj = table_obj.counters[counter_id]
							setattr(counter_obj, config['attribute'], config['value'])
							break
		except Exception:
			pass
		