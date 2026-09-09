__doc__ = \
	__version__ = '1.0'
__authors__ = [
	'Version 0.1: Gil Martins <gil-l-martins@alticelabs.com>'
]

# from xml.etree.ElementTree import Element
import xml.etree.ElementTree as ET


'''
"operationsCatalog" :
		{
			"unit" :
			{
				"truncateValue": [
					{
						"id": "RESERVEDBY",
						"startIndex": 0,
						"endIndex": 2900,
						"newFields": ["RESERVEDBY"],
						"units":["ACLIPV4","ACLIPV6"]
					},
					{
						"id": "PUBLICKEY",
						"startIndex": 0,
						"endIndex": 2900,
						"newFields": ["PUBLICKEY", "EXTRAFIELD"],
						"optional": true
					}
				]
			},
			"item" :
			{
			}
		}
'''


def process(element, unit_obj, config):
	
	try:
		# check for 'units' in config to filter units to apply
		all_units = True
		if 'units' in config and isinstance(config['units'], list):
			all_units = False
			config['units'] = [str(x).upper() for x in config['units']]
		
		if not all_units:
			if unit_obj.ossId.upper() not in config['units']:
				return
		
		# apply truncate operation if field exists
		found = False
		for counter_id in unit_obj.attributes.keys():
			if config['id'].upper() == counter_id.upper():
				found = True
				add_truncate_operation(element, config, counter_id)
				break
		
		if not found:
			for table_id in unit_obj.tables:
				table_obj = unit_obj.tables[table_id]
				
				for counter_id in table_obj.counters.keys():
					if config['id'].upper() == counter_id.upper():
						add_truncate_operation(element, config, counter_id)
						break
	except Exception:
		pass


def add_truncate_operation(element, config, counter_id):
	column = element.find(".//item[@id='{0}']".format(counter_id))
	if not column:
		column = ET.Element('item')
		column.set('id', counter_id)
		element.append(column)
	op = ET.SubElement(column, 'operation')
	op.set('type', 'truncateValue')
	if 'optional' in config:
		op.set('optional', str(config['optional']))
	op_def = ET.SubElement(op, 'def')
	op_def.set('startIndex', str(config['startIndex']))
	op_def.set('endIndex', str(config['endIndex']))
	config['newFields'] = move_to_last(config['newFields'], config['id'])
	for key in config['newFields']:
		new_field = ET.SubElement(op_def, 'newField')
		new_field.text = key.upper()


def move_to_last(new_fields, item):
	item = item.upper()
	new_fields = [x.upper() for x in new_fields]
	new_fields = list(set(new_fields))
	if item in new_fields:
		idx = new_fields.index(item)
		new_fields = new_fields[:idx] + new_fields[idx+1:] + [new_fields[idx]]
	return new_fields
	