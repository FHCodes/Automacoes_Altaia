#!/usr/bin/env python

__doc__ = \
"""
This module aggregates ALB AAA xml files into a single CSV files
"""

__version__ = "1.0"

__authors__ = "Version 1.0: Paulo Gil<paulo-a-gil@alticelabs.com>"

import os
import re
import pickle
import argparse
from datetime import datetime
import xml.etree.ElementTree as ET

class AlticeLabsAAAPreProcessor(object):

	# Init class with indir and outdir paths
	def __init__(self, indir, outdir):
		self._indir = indir
		self._outdir = outdir

		# Pickle load processed file list, if exists
		self._processed_files = list()
		if os.path.exists(os.path.join(self._indir,"processed_files")):
			self._processed_files = pickle.load(open(os.path.join(self._indir,"processed_files"), "rb"))

		# Translate IF and DF into TRAFFIC and DISK
		self._config = {"IF": "TRAFFIC", "DF": "DISK"}


	# Do nothing with __enter__
	def __enter__(self):
		return self


	# Picke dump on __exit__
	def __exit__(self, exc_type, exc_val, exc_tb):
		with open(os.path.join(self._indir,"processed_files"), "wb") as f:
			pickle.dump(self._processed_files, f)
		f.close()


	# Convert UNIX timestamp into a friendly format 
	def convertTimestamp(self, timestamp):
		return datetime.strftime(datetime.fromtimestamp(timestamp), "%Y-%m-%d %H:%M:%S")


	# Export dictionary to a CSV file
	def export(self, unit_data, unit_name):
		for hostname in unit_data:
			for collection_time in unit_data[hostname]:
				formatted_timestamp = self.convertTimestamp(int(collection_time)).replace("-","").replace(" ","").replace(":","")
				filename = "{0}-{1}-{2}.csv".format(hostname,unit_name,formatted_timestamp)
				f = open(os.path.join(self._outdir,filename), "a")

				granularity = unit_data[hostname][collection_time]["step"]
				endtime = unit_data[hostname][collection_time]["end"]
				header = "measurement,aaa,starttime,endtime,granularityperiod,"
				values = "{0},{1},{2},{3},{4},".format(unit_name,hostname,self.convertTimestamp(int(collection_time)),self.convertTimestamp(int(endtime)),granularity)

				# Process header according to unit ID
				if unit_name == "AAA-REQ":
					for item in unit_data[hostname][collection_time]["counters"]:
						header = header + ",".join(unit_data[hostname][collection_time]["counters"][item].keys()) + "\n"
						break
				else:
					header = header + ",".join(unit_data[hostname][collection_time]["counters"].keys()) + "\n"
				
				# Write header to CSV file
				f.write(header)

				# Process and write lines according to unit ID
				if unit_name == "AAA-REQ":
					for svc in unit_data[hostname][collection_time]["counters"]:
						values_to_write = values + ','.join(unit_data[hostname][collection_time]["counters"][svc].values()) + "\n"
						f.write(values_to_write)
				else:
					values_to_write = values + ','.join(unit_data[hostname][collection_time]["counters"].values()) + "\n"
					f.write(values_to_write)
	

	# Process AAA-REQ unit datta
	def processAaaReq(self, subdir, filename, global_unit_data, hostname, measurement_item, request_type, service_type):
		measurement_id = measurement_item.upper()

		if measurement_id in self._config.keys():
			measurement_id = self._config[measurement_id]

		if measurement_id not in global_unit_data:
			global_unit_data[measurement_id] = dict()

		if hostname not in global_unit_data[measurement_id]:
			global_unit_data[measurement_id][hostname] = dict()

		# Parse file into ElementTree      
		try:
			tree = ET.parse(os.path.join(subdir, filename))
			root = tree.getroot()
		except:
			print('Error: ', os.path.join(subdir, filename))

		# Counters are static in this context
		counters = ["request","error","success"]
		values = dict()

		# Extract start time, end time and granularity
		for meta_tag in root.findall("meta"):
			for row in meta_tag:
				if row.tag == "start":
					start_time = row.text
				elif row.tag == "end":
					end = row.text
				elif row.tag == "step":
					step = row.text
		
		# Append "sum" to counter name 
		counters = ["{0}-{1}".format("sum",x) for x in counters]
		
		# Process tree again to extract values
		for data in root.findall("data"):
			for data_row in data.findall("row"):
				for row in data_row:
					if row.tag == "t":
						start = row.text
						if start_time == start:
							if start not in values:
								values[start] = []
							if start not in global_unit_data[measurement_id][hostname]:
								global_unit_data[measurement_id][hostname][start] = dict()
								global_unit_data[measurement_id][hostname][start]["step"] = step
								global_unit_data[measurement_id][hostname][start]["end"] = int(end) + int(step)
								global_unit_data[measurement_id][hostname][start]["counters"] = dict()
							if service_type not in global_unit_data[measurement_id][hostname][start]["counters"]:
								global_unit_data[measurement_id][hostname][start]["counters"][service_type] = dict()
								for counter in counters:
									global_unit_data[measurement_id][hostname][start]["counters"][service_type].update({counter: ""})
					elif row.tag == "v":
						if start_time == start:
							v = row.text
							if row.text != "NaN":
								v = "{:f}".format(float(row.text))
							values[start].append(v if v != "NaN" else "")
		
		# Update final dict with counter/value pairs
		for start in values:
			global_unit_data[measurement_id][hostname][start]["counters"][service_type].update(dict(zip(["service-type"],[service_type])))
			global_unit_data[measurement_id][hostname][start]["counters"][service_type].update({"sum-{0}".format(request_type): values[start][0]})
	
	# Search for files in indir and process them
	def process(self):
		global_unit_data = dict()
		
		# Loop through files in indir
		for subdir, dirs, files in os.walk(self._indir):
			for filename in files:
				# Process only XML files
				if ".xml" in filename:
					# Skip already processed file
					if filename in self._processed_files:
						continue
					
					# Add filename to processed_files
					self._processed_files.append(filename)
					
					# Apply regex to extract info from filename
					filenameRegex = re.compile(r"^(?P<HOSTNAME>[a-zA-Z0-9]+-?\d+)-(?P<ITEM>.+)-[a-z]-(?P<TIMESTAMP>\d+).xml").match(filename)
					
					if filenameRegex:
						hostname = filenameRegex.group("HOSTNAME")
						measurement_item = filenameRegex.group("ITEM")
						measurement_item = measurement_item.replace("_","-")
						measurement_item = measurement_item.replace("--","-")
					else:
						# If first regex fails, apply a second one to match AAA-REQ files
						filenameRegex = re.compile(r"^(?P<HOSTNAME>[^-]+)-(?P<UNIT>aaa-req)-(?P<SERVICETYPE>.+)-(?P<REQUESTTYPE>request|success|error)-(?P<TIMESTAMP>\d+).xml").match(filename)
						if filenameRegex:
							hostname = filenameRegex.group("HOSTNAME")
							measurement_item = filenameRegex.group("UNIT")
							measurement_item = measurement_item.replace("_","-")
							measurement_item = measurement_item.replace("--","-")
							service_type = filenameRegex.group("SERVICETYPE")
							request_type = filenameRegex.group("REQUESTTYPE")

					# Process file according to unit ID
					if "aaa-req" in measurement_item:
						self.processAaaReq(subdir, filename, global_unit_data, hostname, measurement_item, request_type, service_type)
					else:
						# Get counter name from measurement item
						counter_name = "-".join(measurement_item.split("-")[1:])

						# Find measurement ID from measurement item
						unit_id = measurement_item.split("-")[0]
						measurement_id = unit_id.upper()

						if measurement_id in self._config.keys():
							measurement_id = self._config[measurement_id]

						if measurement_id not in global_unit_data:
							global_unit_data[measurement_id] = dict()

						if hostname not in global_unit_data[measurement_id]:
							global_unit_data[measurement_id][hostname] = dict()

						# Parse file into ElementTree
						tree = ET.parse(os.path.join(subdir, filename))
						root = tree.getroot()

						counters = []
						values = dict()

						# Extract start time, end time, granularity and counter suffix
						for meta_tag in root.findall("meta"):
							for row in meta_tag:
								if row.tag == "start":
									start_time = row.text
								elif row.tag == "end":
									end = row.text
								elif row.tag == "step":
									step = row.text
								elif row.tag == "legend":
									for entry in row.findall("entry"):
										counters.append(entry.text)

						# Append suffix to counter names
						counters = ["{0}-{1}".format(counter_name,x) for x in counters]
						
						# Process tree again to extract values
						for data in root.findall("data"):
							for data_row in data.findall("row"):
								for row in data_row:
									if row.tag == "t":
										start = row.text
										if start_time == start:
											if start not in values:
												values[start] = []
											#if start not in global_unit_data[measurement_id][hostname][collection_type]:
											if start not in global_unit_data[measurement_id][hostname]:
												global_unit_data[measurement_id][hostname][start] = dict()
												global_unit_data[measurement_id][hostname][start]["step"] = step
												global_unit_data[measurement_id][hostname][start]["end"] = int(end) + int(step)
												global_unit_data[measurement_id][hostname][start]["counters"] = dict()
									elif row.tag == "v":
										if start_time == start:
											v = row.text
											if row.text != "NaN":
												v = "{:f}".format(float(row.text))
											values[start].append(v if v != "NaN" else "")
						
						# Update final dict with counter/value pairs
						for start in values:
							global_unit_data[measurement_id][hostname][start]["counters"].update(dict(zip(counters,values[start])))

		# Export data to CSV files after processing XML files
		for measurement_id in global_unit_data:
			self.export(global_unit_data[measurement_id], measurement_id)

if __name__ == "__main__":

	# Handle program arguments
	parser = argparse.ArgumentParser(description='Preprocess AlticeLabs AAA PM files.')
	parser.add_argument("-i", "--indir", help='The input directory', required=True)
	parser.add_argument("-o", "--outdir", help='the output directory', required=True)
	args = parser.parse_args()

	# Get indir and outdir from arguments
	indir = args.indir
	outdir = args.outdir

	# Call AlticeLabsAAAPreProcessor to init processing procedure
	with AlticeLabsAAAPreProcessor(indir, outdir) as preprocessor:
		preprocessor.process()
