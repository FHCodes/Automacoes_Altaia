__doc__ = \
	__version__ = '1.0'
__authors__ = ['Version 0.1: Bruno Silva <bruno-e-silva@alticelabs.com>']

def process(baseElement, newElement):
	
	for newOp in newElement.findall('operation'):
		if newOp.get('type') == 'applyRegex':
			
			# first check if the operation exists in the previous
			# (avoids replication when there is the exact same operation already)
			newOp_exists = False
			for baseOp in baseElement.findall('operation'):
				if is_equal_operation(baseOp, newOp):
					newOp_exists = True
					break
			
			if not newOp_exists:
				for baseOp in baseElement.findall('operation'):
					if baseOp.get('type') == 'applyRegex':
						for newRegex in newOp.findall('regex'):
							pos = 0
							missingPattern = True
							for baseRegex in baseOp.findall('regex'):
								if baseRegex.get('pattern') == newRegex.get('pattern'):
									missingPattern = False
									for newField in newRegex.findall('newField'):
										missingNewField = True
										for baseField in baseRegex.findall('newField'):
											if baseField.text == newField.text:
												missingNewField = False
										if missingNewField:
											baseRegex.append(newField)
							if missingPattern:
								for lRegex in baseOp.findall('regex'):
									if len(newRegex.findall('newField')) >= len(lRegex.findall('newField')):
										baseOp.insert(pos, newRegex)
										missingPattern = False
										break
									pos += 1
								if missingPattern:
									baseOp.insert(pos, newRegex)


def is_equal_operation(e1, e2):
	if e1.tag != e2.tag:
		return False
	if e1.attrib != e2.attrib:
		return False
	if len(e1._children) != len(e2._children):
		return False
	for i in range(len(e1._children)):
		if e1._children[i].attrib != e2._children[i].attrib:
			return False
		if e1._children[i].tag != e2._children[i].tag:
			return False
	if len(e1) != len(e2):
		return False
	return all(is_equal_operation(c1, c2) for c1, c2 in zip(e1, e2))
