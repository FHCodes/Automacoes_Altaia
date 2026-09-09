#!/usr/bin/env python

__doc__ = \
    '''
	This is a very flexible catalog operation that allows to write code in the xml operations catalog and execute it in Python.

	INPUTS: Optional and variable. Are kept in a dictionary and validated against the documents of the familyObject, since they must exist
	in the documents. They are replaced in the code snippet according to their id, allowing for multiple utilizations of the same input.

	OUTPUT: Mandatory and fixed. Must only be one, but does not have to be present in the documents of the FamilyObject (allowing for generation
	of a new column in the final table.

	CODE: Mandatory. The python code to be executed. Must have xml special characters escaped (ampersand (&)->&amp; less than (<)->&lt;
	greater than (>)->&gt;)
	If existing, input placeholders must follow the format #ID#
'''

__version__ = '0.1'

__authors__ = [
    "Version 0.1: Joao Pio <joao-t-pio@telecom.pt>"
]

# Native libraries
import importlib

# Local libraries
logger = importlib.import_module("shelf.collectorprocess.logger").logger


def process(info, baseObject={}):
    unitID = info["familyObj"].getUnitID()

    input_dict = dict()

    # sample document for input validation
    sample_document = info["familyObj"].getDocuments()
    if len(sample_document) == 0:
        # empty document list. Move on
        return info["familyObj"]
    else:
        # get just one document
        sample_document = sample_document[0]

    # Validate the inputs
    for input in info["operation"].findall("input"):

        if input.text is None:
            logger.warning("executeCode: Input is empty in family '{}'".format(unitID))
            return info["familyObj"]

        if input.text.upper() in sample_document.keys():
            # {"1": "columnName"}
            input_dict[input.attrib["id"]] = input.text.upper()
        else:
            logger.warning("executeCode: Key '{}' not found in document".format(input.text.upper()))
            return info["familyObj"]

    if info["operation"].findall("input") == []:
        logger.warning("executeCode: No inputs defined in family '{}'".format(unitID))
        return info["familyObj"]

    # get the output
    output = info["operation"].find("output")

    if output == None:
        logger.warning("Missing output definition in catalog operation.")
        return info["familyObj"]
    elif output.text is None:
        logger.warning("Output definition is empty in catalog operation.")
        return info["familyObj"]

    # get the code string
    code = info["operation"].find("code")

    if code == None:
        logger.warning("Missing code string in catalog operation.")
        return info["familyObj"]
    else:
        code = code.text

    # code treatment
    tokenized_code = code.split("#")

    # Altered documents list
    new_documents = list()

    # Replace code tokens with values from documents
    for document in info["familyObj"].getDocuments():

        executable_code = ""

        for cnt, token in enumerate(tokenized_code):
            # It's a token
            if cnt % 2 != 0:
                if token in input_dict.keys():
                    token = document[input_dict[token]]
                    executable_code = "{0}'{1}'".format(executable_code, token)
                else:
                    # Token not found
                    logger.warning("executeCode: Token '{0}' not found in document of family {1}".format(token, unitID))
                    continue
            else:
                executable_code = "{0}{1}".format(executable_code, token)

        try:
            result = eval(executable_code)
            document[output.text.upper()] = result
            new_documents.append(document)
        except:
            # With an invalid code, no point repeating the operation for other documents.
            logger.warning("executeCode: Invalid code {}".format(executable_code))
            return info["familyObj"]

    info["familyObj"].setDocuments(new_documents)

    return info["familyObj"]
