#!/usr/bin/env python

__doc__ = \
	'''
This module breaks Ericsson format performance/parameter files that follow the following schemas:
utranNrm.xsd
genericNrm.xsd
geranNrm.xsd
configData.xsd
EricssonSpecificAttributes.xx.xx.xsd

The resulting files are separated according to their context (Subnetwork or MeContext)
'''

__version__ = '0.1'

__authors__ = ["Version 2.0: Joao Pio <joao-t-pio@telecom.pt>"]

import sys, re, os, time

from xml.sax import saxutils, handler, make_parser, parse
import argparse
import collections
import pickle
from datetime import datetime


class EricssonContentHandler(handler.ContentHandler):

	def __init__(self, datetime, outdir, verbose, outSN, outMC, escape):

		self._filesCreated = 0

		self._datetime = datetime

		self._isHeader = False

		self._isSubNetwork = False
		self._isMeContext = False

		self._Child = None
		self._Parent = None
		self._deleteZone = False

		# Used to detect self terminated nodes
		self._selfTerminatedNode = False

		# Header that will be copied by all output files
		self._globalHeader = []  # List because it retains order of insersion (hierarchy is saved)
		# Footer that will be copied by all output files
		self._globalFooter = []

		# List of subnetwork type file handlers
		self._subNetworkFilesQueue = []
		# List of mecontext type file handlers
		self._meContextFilesQueue = []

		self._outDir = outdir
		self._verbose = verbose
		self._escape = escape
		self._outSN = outSN
		self._outMC = outMC

		self._parseStats = {"Total": collections.Counter(SubNetworkFiles=0, MeContextFiles=0)}
		self._parseStartTime = None

	def startDocument(self):

		if self._parseStartTime is None:
			self._parseStartTime = datetime.now()

		print "Starting to process file: {}".format(str(datetime.now()))

	def endDocument(self):
		print "Finished processing file"

		self.printStats()

	def printStats(self):

		print '------------------------------------------------------------------------------------'
		print '--------- Parsing Started: {}'.format(str(self._parseStartTime))
		print '--------- Parsing finished: {}'.format(str(datetime.now()))
		print '--------- Execution time: {}'.format(str(datetime.now() - self._parseStartTime))
		print ""
		print '--------- Statistics:'
		print '--------- SubnetWork Files -----> {}'.format(self._parseStats["Total"]["SubNetworkFiles"])
		print '--------- MeContext Files -----> {}'.format(self._parseStats["Total"]["MeContextFiles"])
		print '------------------------------------------------------------------------------------'

	def startElementNS(self, name, qname, attrs):

		attrs_no_ns = dict()

		# Convert NameSpace attributes to simple attributes
		for a in attrs.items():
			attrs_no_ns[a[0][1]] = a[1]

		# Define parent
		self._Parent = self._Child

		self._Child = name[1]

		if name[1] in ["bulkCmConfigDataFile", "configData", "SubNetwork"]:
			# Start build the GlobalHeader
			self._isHeader = True
			self._globalHeader.append({"name": name[1], "selfterminated": False, "attrs": attrs_no_ns})
			# self._globalHeader.append("\n")
			self._globalFooter.append({"name": name[1], "selfterminated": False, "attrs": {}})

			if name[1] == "bulkCmConfigDataFile":
				self._globalFooter.append(
					{"name": "fileFooter", "selfterminated": True, "attrs": {"dateTime": "{}".format(self._datetime)}})

			if name[1] == "SubNetwork":
				self._isHeader = False
				self._isSubNetwork = True

				# Validates that SubNetwork files are a desired output
				if self._outSN:

					# Subnetwork nodes signal the start of a file of external families
					filename = self.getFilename(self._outDir)

					if self._verbose:
						print "SN: Opening file {}".format(filename)

					# Open the file
					self._subNetworkFilesQueue.append(open(filename, 'w'))

					# update stats
					self._parseStats["Total"].update({'SubNetworkFiles': 1})

					# print "-------------------------------------------------"

					# print "SN: WRITE HEADER FOR FILE {}".format(filename)

					self.writeHeader(self._subNetworkFilesQueue[-1])

		elif name[1] == "fileHeader":
			# File header is self terminated
			self._globalHeader.append({"name": name[1], "selfterminated": True, "attrs": attrs_no_ns})
		# self._globalHeader.append("\n")

		# MeContext nodes signal the start of a file
		elif name[1] == "MeContext":
			self._isHeader = True
			# Start build the GlobalHeader
			self._globalHeader.append({"name": name[1], "selfterminated": False, "attrs": attrs_no_ns})
			# self._globalHeader.append("\n")
			self._globalFooter.append({"name": name[1], "selfterminated": False, "attrs": {}})

			self._isMeContext = True

			# Validates that SubNetwork files are a desired output
			if self._outMC:
				# build new file name
				filename = self.getFilename(self._outDir)

				if self._verbose:
					print "MC: Opening file {}".format(filename)
				# Open the file
				self._meContextFilesQueue.append(open(filename, 'w'))

				# update stats
				self._parseStats["Total"].update({'MeContextFiles': 1})

				# write the header
				self.writeHeader(self._meContextFilesQueue[-1])

		# Branch to exclude certain nodes already addressed, from the all other nodes branch
		elif name[1] in ["fileFooter"]:
			pass

		# Remove attributes from MeContext
		elif name[1] in ["attributes"] and self._Parent == "MeContext":
			self._deleteZone = True
			# print "self._deleteZone = True"
			pass

		# All other possible nodes
		else:
			self._isHeader = False
			self._selfTerminatedNode = True

			# Build the nodedict
			nodedict = {"name": name[1], "selfterminated": False, "attrs": attrs_no_ns}

			# Is a Subnetwork type file
			if self._isSubNetwork == True and self._isMeContext == False and self._deleteZone == False:
				if self._outSN:
					self.writeNode(nodedict, self._subNetworkFilesQueue[-1])
				else:
					pass
			# Is a MeContext type file (might be inside a SubNetwork node)
			elif self._isMeContext == True and self._deleteZone == False:
				if self._outMC:
					self.writeNode(nodedict, self._meContextFilesQueue[-1])
				else:
					pass

		# print "{0} ---- {1}".format(name[1], attrs_no_ns)

	def endElementNS(self, name, qname):

		if name[1] == "SubNetwork":
			if self._outSN:
				# Write the footer
				self.writeFooter(self._subNetworkFilesQueue[-1])

				# Close the file
				self._subNetworkFilesQueue[-1].close()

				# Pop all the lists affected by this node
				self._subNetworkFilesQueue.pop()
			self._globalHeader.pop()
			# pops the line break
			# self._globalHeader.pop()
			self._globalFooter.pop()

			self._isSubNetwork = False

		elif name[1] == "MeContext":
			if self._outMC:
				# Write the footer
				self.writeFooter(self._meContextFilesQueue[-1])

				# Close the file
				self._meContextFilesQueue[-1].close()

				# Pop all the lists affected by this node
				self._meContextFilesQueue.pop()

			self._globalHeader.pop()
			# pops the line break
			# self._globalHeader.pop()
			self._globalFooter.pop()

			self._isMeContext = False

		# Branch to exclude certain nodes already addressed, from the all other nodes branch
		elif name[1] in ["bulkCmConfigDataFile", "configData", "fileHeader", "fileFooter"]:
			pass
		# All other possible nodes
		else:

			if self._deleteZone:
				if name[1] == "attributes":
					self._deleteZone = False
				# print "self._deleteZone = False"
				return

			# Build the nodedict
			nodedict = {"name": name[1], "selfterminated": self._selfTerminatedNode, "attrs": {}}

			# Is a Subnetwork type file
			if self._isSubNetwork == True and self._isMeContext == False:
				if self._outSN:
					self.writeNodeEnd(nodedict, self._subNetworkFilesQueue[-1])
				else:
					pass
			# Is a MeContext type file
			elif self._isMeContext:
				if self._outMC:
					self.writeNodeEnd(nodedict, self._meContextFilesQueue[-1])
				else:
					pass

	def characters(self, content):

		# always resets self terminated node flag
		self._selfTerminatedNode = False

		if self._isHeader:
			# removes changes of lines between the xml nodes
			# if re.match("^\s+$", content) == None:
			pass
		# self._globalHeader.append(content)
		# Is a subnetwork type file, outside mecontext nodes
		elif self._isSubNetwork and not self._isMeContext:
			# removes changes of lines between the xml nodes
			# if re.match("^\s+$", content) == None:

			try:
				if self._outSN:
					if self._escape:
						self._subNetworkFilesQueue[-1].write(saxutils.escape(content))
					else:
						self._subNetworkFilesQueue[-1].write(content)
				else:
					pass
			except:
				pass
		# Is a mecontext type file, possibly inside a subnetwork node
		elif self._isMeContext and self._deleteZone == False:
			try:
				if self._outMC:
					if self._escape:
						self._meContextFilesQueue[-1].write(saxutils.escape(content))
					else:
						self._meContextFilesQueue[-1].write(content)
				else:
					pass
			except:
				pass

	def getFilename(self, outdir):

		hierarchy = []

		for node in self._globalHeader:
			try:
				hierarchy.append((node["name"], node["attrs"]["id"]))
			# Nodes without id are skipped
			except:
				continue

		return os.path.join(outdir, ",".join("=".join(list(level)) for level in hierarchy) + ".xml")

	# Write the xml header for the specific file
	def writeHeader(self, filehandler):

		tabs = lambda i: "".join(['\t'] * i)
		newline = lambda j: '\n' if j != 0 else ""
		# blanks = lambda i: "".join(['\n'] + ['\t']*i)

		# print "------------------HEADER----------------------"
		index = 0
		for line in self._globalHeader:

			# differentiates between the dictionary (a node) and string (line changes)
			if type(line) == dict:

				filehandler.write(newline(index))
				filehandler.write(tabs(index))

				try:
					filehandler.write("<{}".format(line["name"]))
					for (attrname, value) in line["attrs"].items():
						filehandler.write(' {0}="{1}"'.format(attrname, saxutils.escape(value)))

					if line["selfterminated"]:
						filehandler.write('/>')
					else:
						filehandler.write('>')
						# Closed tag nodes are indented
						index += 1
				except:
					continue

		filehandler.write(newline(index))
		filehandler.write(tabs(index))

	# print "------------------END HEADER----------------------"

	def writeFooter(self, filehandler):

		tabs = lambda i: "".join(['\t'] * i)
		newline = lambda j: '\n' if j != 0 else ""

		footerSize = len(self._globalFooter) - 2

		for ind, line in enumerate(reversed(self._globalFooter)):

			filehandler.write(newline(ind))
			if ind != 0:
				if line["selfterminated"]:
					filehandler.write(tabs(footerSize + 1))
				else:
					filehandler.write(tabs(footerSize))

			# Start tag
			if line["selfterminated"]:
				# Write the blanks spaces
				# filehandler.write(blanks(footerSize-1))

				filehandler.write("<{}".format(line["name"]))

			else:
				# Write the blanks spaces
				# filehandler.write(blanks(footerSize))

				filehandler.write("</{}".format(line["name"]))

			# Attributes
			for (attrname, value) in line["attrs"].items():
				filehandler.write(' {0}="{1}"'.format(attrname, saxutils.escape(value)))

			# End tag
			if line["selfterminated"]:
				filehandler.write('/>')
			else:
				filehandler.write('>')

			footerSize -= 1

	def writeNode(self, nodedict, filehandler):

		filehandler.write("<{}".format(nodedict["name"]))
		for (attrname, value) in nodedict["attrs"].items():
			filehandler.write(' {0}="{1}"'.format(attrname, saxutils.escape(value)))

		if nodedict["selfterminated"]:
			filehandler.write('/>')
		else:
			filehandler.write('>')

	def writeNodeEnd(self, nodedict, filehandler):

		# If node is self terminated, must rewind the file handler to delete the end of the start node
		if nodedict["selfterminated"]:
			filehandler.seek(-1, os.SEEK_END)
			filehandler.truncate()
			filehandler.write("/>")
		# It's a normal closed tag node
		else:
			filehandler.write("</{}".format(nodedict["name"]))
			filehandler.write(">")


def filename_to_datetime(filename):
	datematch = re.match("^.*?_(\d+)\.xml", filename)

	if datematch is not None:
		dt = time.strptime(datematch.group(1), "%Y%m%d")
		dt = time.strftime("%Y-%m-%dT%H:%M:%SZ", dt)
		return dt
	else:
		return None


def walklevel(folder, level=0):
	folder = folder.rstrip(os.path.sep)

	assert os.path.isdir(folder)

	num_sep = folder.count(os.path.sep)

	for root, dirs, files in os.walk(folder):
		yield root, dirs, files
		num_sep_this = root.count(os.path.sep)

		if num_sep + level <= num_sep_this:
			del dirs[:]


if __name__ == "__main__":

	parser = argparse.ArgumentParser(description='Preprocess ERICSSON Parameter files.')

	# parser.add_argument("file", help='the input file')

	parser.add_argument("indir", help='the input directory')

	parser.add_argument("outdir", help='the output directory')

	parser.add_argument("--head", default=1, type=int, help='Number of files to preprocess')

	parser.add_argument("--depth", default=0, type=int, help='Number of levels to go digging')

	parser.add_argument("context", choices=['SUBNETWORK', 'MECONTEXT', 'ALL'],
						help='Desired output files context level: SUBNETWORK/MECONTEXT/ALL')

	parser.add_argument("-v", "--verbose", action="store_true", default=False, help='increase output verbosity')

	parser.add_argument("--escape", action="store_true", default=False, help='escape XML content')

	args = parser.parse_args()

	# print args

	# Adds trailing slash to path in case user missed it
	indir = os.path.join(args.indir, '')
	outdir = os.path.join(args.outdir, '')
	context = args.context
	verbose = args.verbose
	escape = args.escape
	head = abs(int(args.head))
	depth = abs(int(args.depth))

	print "\n\n#######################START##################################\n"

	if not os.path.isdir(indir):
		print "ERROR: Input folder '{}' does not exist.".format(indir)
		sys.exit()

	if not os.path.isdir(outdir):
		print "ERROR: Output folder '{}' does not exist.".format(outdir)
		sys.exit()

	if context == "MECONTEXT":
		outMC = True
		outSN = False
	elif context == "SUBNETWORK":
		outMC = False
		outSN = True
	else:
		outMC = True
		outSN = True

	# Checks if there is a list of previously processed files in the input directory
	if os.path.isfile(os.path.join(indir, "preprocessed.list")):
		# Opens file list for reading
		pplistFile = open(os.path.join(indir, "preprocessed.list"), 'rb')
	else:
		# creates file list
		pplistFile = open(os.path.join(indir, "preprocessed.list"), 'wb+')

	filelist = []
	pplist = []

	try:
		# read
		pplist = pickle.load(pplistFile)

		if verbose:
			print "\n\n---------------------------------------------\n-------- Previously processed files list:\n"
			print pplist
			print "\n---------------------------------------------\n"

		# for basedir, subdirs, filenames in os.walk(indir):
		for basedir, subdirs, filenames in walklevel(indir, depth):

			# reached file limit (head = 0)
			if not head:
				break

			for filename in filenames:
				# Ignore the preprocessed list of filenames
				if "preprocessed.list" in filename:
					continue

				# reached file limit
				if not head:
					break

				# Removes the extension for comparison to avoid problems with added suffixes
				name, extension = os.path.splitext(filename)

				# Compressed files need to have the extension removed twice
				if extension in [".gz", ".gz_processed"]:
					name, extension = os.path.splitext(name)

				if name not in pplist:
					filelist.append(os.path.join(basedir, filename))
					# print "added {} to the process list".format(os.path.join(basedir, filename))
					head -= 1

	except Exception as e:

		# Walk the folder finding all files
		# filelist = [os.path.join(dp, f) for dp, dn, fn in os.walk(indir) for f in fn]
		filelist = [os.path.join(dp, f) for dp, dn, fn in walklevel(indir, depth) for f in fn]
		# Excludes preprocessed.list
		filelist = [f for f in filelist if not f.endswith("preprocessed.list")]
		# Only include the number of files that were provided in "head" argument
		filelist = filelist[:head]
		if verbose:
			print "No previous processed files detected. Processing all files.\n"
			print filelist

	# close preprocessed files list
	pplistFile.close()

	for filename in filelist:

		dt = filename_to_datetime(os.path.basename(filename))

		if dt is not None:

			# Create Ericsson custom handler
			erichandler = EricssonContentHandler(dt, outdir, verbose, outSN, outMC, escape)

			# create a parser
			xml_parser = make_parser()

			# Set the custom handler as the parser's handler
			xml_parser.setContentHandler(erichandler)
			# Activate namespace processing
			xml_parser.setFeature(handler.feature_namespaces, True)
			# xml_parser.setFeature(handler.feature_namespace_prefixes, True)

            try:
                xml_parser.parse(filename)
            except:
                print "ERROR: Couldn't treatment file because is empty or his format not is correctly: {}".format(os.path.basename(filename))
                print "Finished processing file"
                continue
		# Could not get the date from the filename
		else:
			if verbose:
				print "ERROR: Couldn't get datetime from filename: {}".format(os.path.basename(filename))

		# Removes the extension for comparison to avoid problems with added suffixes
		name, extension = os.path.splitext(os.path.basename(filename))

		# Compressed files need to have the extension removed twice
		if extension in [".gz", ".gz_processed"]:
			name, extension = os.path.splitext(name)

		# Add the newly processed files list to the already processed files list
		pplist = pplist + [name]

		# update file list (it's opened with 'w' because the filelist has been loaded from the file before, so no need to append)
		pplistFile = open(os.path.join(indir, "preprocessed.list"), 'wb')
		pickle.dump(pplist, pplistFile)
		pplistFile.close()
