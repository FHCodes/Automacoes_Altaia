#!/usr/bin/env python

__doc__ = \
	'''
	Nokia 3GPP 32.432 Performance XML reader

	Spec file syntax:
	<operation type="Readers" name="NOKIA.3GPP.32_432" />

	Example sample:
	<mdc xmlns:HTML="http://www.w3.org/TR/REC-xml">
	<mfh>
		<cbt>20221117150000-0200</cbt>
	</mfh>
	<md>
		<neid>
			<neun>152807,HNBId=001D4C-4214240703,Fsn=4214240703,bSRName=CARTAO DE TODOS ITAPETININGA LTDA,manualPscUsed=true</neun>
			<nedn>SubNetwork=SAM,SubNetwork=FemtoBSR,SubNetwork=2,ManagedElement=28070,bsrFunction=0</nedn>
			<nesw>Ev2.2-250mW-32-21-2, 250mW - 2100MHz - 8 User License, BSR-15.01.142, openAccess</nesw>
		</neid>
		<sf>false</sf><mts>20221117160000-0200</mts>
		<gp>3600</gp>
		<mn> NumofDownLinkUserBitsforPSDL64kbpsDataRateaboveRLC
			<mt>NumUserBits_PS64DL
				<mv>0 </mv>
			</mt>
		</mn>
		<mn> NumofDownLinkUserBitsforPSDL64kbpsDataRateaboveRLC
			<mt>NumUserBits_PS64DL
				<mv>
					<moid>... </moid>
					<r>0 </r>
				</mv>
			</mt>
		</mn>
		<mi>
			<mt>VS.sduReceivedFromPdcp</mt>
			<mt>VS.pduTransmittedToMac</mt>
			<mt>VS.sduTransmittedToPdcp</mt>
			<mt>VS.pduReceivedFromMac</mt>
			<mv>
				<moid>plmnId=72404,HenBId=37251,crnti=296</moid>
				<r>3661745</r>
				<r>3544420</r>
				<r>1813487</r>
				<r>1820669</r>
			</mv>
		</mi>
	</md>
'''

__version__ = '1.0'

__authors__ = [
	"Version 0.1: Gil Martins <gil-l-martins@alticelabs.com>"
]

# Native libraries
import xml.etree.cElementTree as ET
import os
from datetime import datetime
import importlib
import io

# Local libraries
BaseOperator = importlib.import_module("shelf.collectorprocess.operators.BaseOperator").BaseOperator
FamilyObject = importlib.import_module("shelf.collectorprocess.operators.FamilyObject").FamilyObject
logger = importlib.import_module("shelf.collectorprocess.logger").logger


class Operator(BaseOperator):

	# Class Constructor
	def __init__(self, operationParams, baseObject={}):
		BaseOperator.__init__(self, operationParams, baseObject=baseObject)

	@staticmethod
	def get_elements(filename_or_file, tag):
		context = iter(ET.iterparse(filename_or_file, events=('start', 'end')))
		_, root = next(context)  # get root element
		for event, elem in context:
			if '}' in elem.tag:
				targettag = elem.tag.rsplit("}", 1)[-1]
			else:
				targettag = elem.tag

			if event == 'end' and targettag == tag:
				yield elem
				root.clear()

	@staticmethod
	def get_node_text(node):
		if not node.text:
			node.text = ""
		else:
			node.text = node.text.strip()
		return node.text

	def process(self, familyObj=FamilyObject(), baseObject={}):

		filesToBeProcessed = familyObj.getFiles()
		familyObj.clearFiles()

		for filePath in filesToBeProcessed:

			fileName = os.path.basename(filePath)
			familyObj.fileName = fileName

			if os.path.getsize(filePath) == 0:
				logger.warning("File {0} is empty.".format(fileName), __file__)
				continue

			# StartTime
			start_time = None
			for cbt in self.get_elements(filePath, 'cbt'):
				start_time = cbt.text.split('-')[0]

			if start_time is None:
				logger.warning(
					"No value in <cbt> node in sample. Impossible obtain startTime \"{}\"".format(
						familyObj.fileName))

			start_time = datetime.strptime(start_time, "%Y%m%d%H%M%S")
			start_time = datetime.strftime(start_time, "%Y-%m-%d %H:%M:%S")

			# EndTime
			end_time = None
			for mts in self.get_elements(filePath, 'mts'):
				end_time = mts.text.split('-')[0]
			end_time = datetime.strptime(end_time, "%Y%m%d%H%M%S")
			end_time = datetime.strftime(end_time, "%Y-%m-%d %H:%M:%S")

			for gp in self.get_elements(filePath, 'gp'):
				granularity = int(self.get_node_text(gp))

			base_document = {'GRANULARITYPERIOD': granularity / 60, 'STARTTIME': start_time, 'ENDTIME': end_time}

			# NEID
			for neid in self.get_elements(filePath, 'neid'):
				base_document['NEUN'] = neid.find('neun').text
				base_document['NEDN'] = neid.find('nedn').text
				base_document['NESW'] = neid.find('nesw').text

			# moid_aggregation : Events with <moid>
			moid_agg = {}

			# 3G data
			unit_id = 'GENERIC_3G'
			mt_list = []
			mv_list = []
			for mn in self.get_elements(filePath, 'mn'):
				for mt in mn.findall('mt'):
					counter_id = self.get_node_text(mt).upper()
					# possibility of multiple <mv> inside an <mt> if <moid> exists for each
					for mv in mt.findall('mv'):
						try:
							# If <moid> has value, it is not added to the envelope and is sent as an alone event to kafka
							moid = self.get_node_text(mv.find('moid'))
							counter_val = self.get_node_text(mv.find('r'))
							try:
								moid_agg[moid]['counter'].append(counter_id)
								moid_agg[moid]['val'].append(counter_val)
							except KeyError:
								moid_agg[moid] = {'counter': [], 'val': []}
								moid_agg[moid]['counter'].append(counter_id)
								moid_agg[moid]['val'].append(counter_val)

						except AttributeError:
							# If <moid> doesn't exist, values are added to list of counters to be sent together in same event to kafka
							counter_val = self.get_node_text(mv)
							mt_list.append(counter_id)
							mv_list.append(counter_val)

			familyObj = self.set_familyObj(mt_list, mv_list, unit_id, base_document, None, familyObj)
			self.nextOp(familyObj=familyObj, baseObject=baseObject)
			familyObj.clearDocuments()

			# Sending events with <moid>
			for moid in moid_agg:
				familyObj = self.set_familyObj(moid_agg[moid]['counter'], moid_agg[moid]['val'], unit_id, base_document, moid, familyObj)
				self.nextOp(familyObj=familyObj, baseObject=baseObject)
				familyObj.clearDocuments()
			# Clear dictionary for 4G data
			moid_agg.clear()

			# 4G data
			unit_id = 'GENERIC_4G'
			for mi in self.get_elements(filePath, 'mi'):
				mt_list = []

				for mt in mi.findall('mt'):
					counter_id = self.get_node_text(mt).upper()
					mt_list.append(counter_id)

				for mv in mi.findall('mv'):
					moid = self.get_node_text(mv.find('moid'))

					try:
						moid_agg[moid]['counter'] += mt_list
						moid_agg[moid]['val'] += [self.get_node_text(r) for r in mv.iter('r')]
					except KeyError:
						moid_agg[moid] = {'counter': [], 'val': []}
						moid_agg[moid]['counter'] += mt_list
						moid_agg[moid]['val'] += [self.get_node_text(r) for r in mv.iter('r')]

			# Sending events with <moid>
			for moid in moid_agg:
				familyObj = self.set_familyObj(moid_agg[moid]['counter'], moid_agg[moid]['val'], unit_id, base_document, moid, familyObj)
				self.nextOp(familyObj=familyObj, baseObject=baseObject)
				familyObj.clearDocuments()
			# Clear dictionary
			moid_agg.clear()

	@staticmethod
	def set_familyObj(mt_list, mv_list, unit_id, base_document, moid=None, familyObj=FamilyObject()):

		if len(mt_list) != len(mv_list):
			logger.warning(
				"Nr of <mt> nodes is different from the nr of <r> nodes \"{0}\"".format(
					familyObj.fileName))
			return familyObj
		else:
			new_document = dict(zip(mt_list, mv_list))
			new_document.update(base_document)

			if moid is not None:
				new_document['MOID'] = moid

			familyObj.setUnitID(unit_id)

			# Prepare mediation message envelope
			try:
				data_time = familyObj.parseEnvelopeDataTime(new_document['STARTTIME'])
			except ValueError as e:
				logger.warning(
					"Could not build mediationEnvelope due to {0}: ".format(
						e), __file__)

			data_document = (
				{"dataTime": data_time, "granularitySec": new_document['GRANULARITYPERIOD'] * 60, "data": new_document})

			familyObj.addDocument(data_document)
			return familyObj
