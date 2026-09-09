#!/usr/bin/env python

# Native libraries
import csv
import argparse
import os
import json
import re
import pickle
from datetime import datetime, timedelta

# get the location of the python source file (avoids errors when running script from other folders)
PATH = os.path.dirname(os.path.abspath(__file__))


# arguments parser
def sandbox_argparse():
    parser = argparse.ArgumentParser(description='Ericsson HLR ".data" file consolidator')

    parser.add_argument("-dn", "--dirname")
    parser.add_argument("-o", "--out")

    # Behaviour flags
    parser.add_argument("-v", "--verbose", action="store_true", default=False, help='increase output verbosity')
    parser.add_argument("-d", "--debug", action="store_true", default=False,
                        help='increase output verbosity to debug mode')
    parser.add_argument("--depth", default=0, type=int, help='Number of levels to go digging')

    arguments = parser.parse_args()

    return arguments


def walklevel(folder, level=0):
    folder = folder.rstrip(os.path.sep)

    assert os.path.isdir(folder)

    num_sep = folder.count(os.path.sep)

    for root, dirs, files in os.walk(folder):
        yield root, dirs, files
        num_sep_this = root.count(os.path.sep)

        if num_sep + level <= num_sep_this:
            del dirs[:]


def index_catalog(catalog):

    out_cat = dict()

    for unit in catalog:
        out_cat[unit] = {int(k): v for k, v in catalog[unit].items()}

    return out_cat


def find_data_files(filter, path):

    data_files = re.compile(filter)

    for root, dirs, files in os.walk(path):
        files_list = []

        for file in files:
            if data_files.match(file) is not None:
                files_list.append(os.path.join(root, file))
        break

    return files_list


if __name__ == '__main__':

    # resolve arguments
    args = sandbox_argparse()

    print "\n\n#######################START##################################\n"
    start_time = datetime.now()
    print "Start time: {0}".format(start_time)

    print "Processing all subfolders of {0}".format(args.dirname)

    # Load HLR catalog with index values for each counter
    with open(os.path.join(os.path.dirname(__file__), "Configs", "HLR_cat.json")) as json_file:
        hlr_cat = index_catalog(json.load(json_file))

    # validate output directory
    if not os.path.exists(args.out):
        raise Exception("Output directory {0} does not exist.".format(args.out))

    # Checks if there is a list of previously processed files in the input directory
    if os.path.isfile(os.path.join(args.dirname, "preprocessed.list")):
        # Opens folder list for reading
        pplistFile = open(os.path.join(args.dirname, "preprocessed.list"), 'rb')
    else:
        # creates folder list
        pplistFile = open(os.path.join(args.dirname, "preprocessed.list"), 'wb+')

    folderlist = []
    pplist = []

    try:
        # read
        pplist = pickle.load(pplistFile)

        if args.verbose:
            print "\n---------------------------------------------\n-------- Previously processed folder list:\n"
            for p in pplist:
                print p
            print "\n---------------------------------------------\n"

        # for basedir, subdirs, filenames in os.walk(indir):
        for basedir, subdirs, filenames in walklevel(args.dirname, args.depth):

            for dir in subdirs:

                if os.path.join(basedir, dir) not in pplist:
                    folderlist.append(os.path.join(basedir, dir))
                    if args.verbose:
                        print "added {0} to the process list".format(os.path.join(basedir, dir))

    except Exception as e:
        # Walk the folder finding all subfolders
        folderlist = [os.path.join(dp, f) for dp, dn, fn in walklevel(args.dirname, args.depth) for f in dn]
        # Excludes preprocessed.list
        if args.verbose:
            print "No previous processed folders detected. Processing all folders.\n"
            if args.verbose:
                for p in folderlist:
                    print p

    # close preprocessed files list
    pplistFile.close()

    folder_cnt = 0
    file_cnt = 0

    for folder in folderlist:

        # data file pattern to extract unit
        data_file_pattern = re.compile("^(([^+]+)\+)*(.*)\..*$")

        dirname_match = re.match("^.*/([^_-]+)-[^/]*$", folder)

        dirname_gran_match = re.match("^.*/.*?(\d+)MIN.*$", folder)

        # Extract network_element_name from folder name provided in the arguments
        if dirname_match is None:
            if args.verbose:
                print "Couldn't extract Network Element Name from folder provided: {0}".format(folder)
            continue

        folder_cnt += 1

        # Extract granularity from folder name provided in the arguments
        if dirname_gran_match is None:
            # Assume default value
            granularity = 15
        else:
            granularity = dirname_gran_match.group(1)
            try:
                granularity = int(granularity)
            except ValueError:
                if args.debug:
                    print "WARNING: Could not recognize granularity {0}. Assuming 15.".format(granularity)
                granularity = 15

        network_element_name = dirname_match.group(1)

        # initialize csv dictionary
        csv_dict = dict()

        data_files = find_data_files(".*\.data", folder)

        for data_file in data_files:
            r = data_file_pattern.match(os.path.basename(data_file))

            if r is None:
                if args.debug:
                    print "WARNING: Could not recognize data file {0}. Skipping.".format(data_file)

            file_cnt += 1

            # extract unit_id
            unit_id = r.group(3)

            try:
                hlr_cat[unit_id]
            except KeyError:
                if args.debug:
                    print "WARNING: Family {0} missing from the catalog".format(unit_id)
                continue

            # build csv header
            header = ["MEASSTARTTIME","MEASENDTIME","NEUSERNAME","NETWORKELEMENTNAME","OBJECTID"]
            for index in hlr_cat[unit_id]:
                header.append(hlr_cat[unit_id][index])

            if unit_id not in csv_dict:
                csv_dict[unit_id.upper()] = [header]

            # extract ne_user_name
            ne_user_name = r.group(2)

            if ne_user_name is None:
                ne_user_name = "CLUSTER"

            # finally open the data file for processing of contents
            with open(data_file) as csvfile:
                csvreader = csv.reader(csvfile, delimiter=',', quotechar='"')

                for row in csvreader:
                    # get fixed columns
                    meas_end_time = row[0]
                    # 20180707120000
                    mst = re.compile(
                        "^(?P<YEAR>[0-9]{2})(?P<MONTH>1[0-2]|0[1-9])(?P<DAY>3[0-1]|0[1-9]|[1-2][0-9])(?P<HOUR>2[0-3]|[0-1][0-9])(?P<MIN>[0-5][0-9])\d*$")

                    mst_match = mst.match(meas_end_time)

                    if mst_match is not None:
                        # Parse the time strings
                        try:
                            meas_end_time = datetime.strptime("{0}{1}{2}{3}{4}".format(mst_match.group(1),mst_match.group(2),mst_match.group(3),mst_match.group(4),mst_match.group(5)), '%y%m%d%H%M')
                            meas_start_time = meas_end_time - timedelta(hours=0, minutes=15)
                        except Exception:
                            if args.debug:
                                print "WARNING: Unexpected format for data field: {0}".format(meas_end_time)
                            continue
                    else:
                        if args.debug:
                            print "WARNING: Unexpected format for data field: {0}".format(meas_end_time)
                        continue

                    if len(row[1]) == 0:
                        object_id = "-"
                    else:
                        object_id = row[1]

                    # Initialize csv row
                    csv_row = [meas_start_time, meas_end_time, ne_user_name, network_element_name, object_id]

                    # get columns according to catalog
                    for index in [x*2 for x in hlr_cat[unit_id].keys()]:
                        try:
                            csv_row.append(row[index])
                        except IndexError:
                            # some counter is out of expected index. Skip but add a comma
                            print "WARNING: counter at index {0} of file {1} is missing".format(index, data_file)

                            csv_row.append("")

                    csv_dict[unit_id.upper()].append(csv_row)

        # write all the csv files
        for unit in csv_dict:
            # build filename
            try:
                file_name = "ERICSSON_CORE_HLR_{0}_{1}_{2}.csv".format(csv_dict[unit][1][3], unit, csv_dict[unit][1][0].strftime("%Y%m%d%H%M"))
            except IndexError:
                if args.debug:
                    print "WARNING: Family {0} has no data".format(unit)
                continue

            file_path = os.path.join(args.out, file_name)

            with open(file_path, 'w') as outcsv:
                writer = csv.writer(outcsv, delimiter=';')
                # header
                writer.writerow(csv_dict[unit][0])

                writer.writerows(csv_dict[unit][1:])

        # Add the newly processed files list to the already processed files list
        pplist = pplist + [folder]

        # update file list (it's opened with 'w' because the filelist has been loaded from the file before, so no need to append)
        pplistFile = open(os.path.join(args.dirname, "preprocessed.list"), 'wb')
        pickle.dump(pplist, pplistFile)
        pplistFile.close()

    end_time = datetime.now()

    print "\nFinished processing: {0}".format(end_time)

    print "\n\n#######################STATISTICS##################################\n"
    print "Folders processed:\t\t\t{0}".format(folder_cnt)
    print "Files processed:\t\t\t{0}".format(file_cnt)
    print "Total duration: {0}".format(str((end_time-start_time)))
