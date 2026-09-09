#!/usr/bin/env python3

__doc__ = \
    '''
'''

__version__ = '1.1'

# Native libraries
import os
import argparse
import sys
from multiprocessing import Process, Queue
import traceback
import json
import importlib

# Local libraries
FlowManager = importlib.import_module("shelf.collectorprocess.flowmanager").FlowManager
Results = importlib.import_module("shelf.collectorprocess.results").Results
logger = importlib.import_module("shelf.collectorprocess.logger").logger
SpecLoader = importlib.import_module("shelf.collectorprocess.collectors.specloader")
pt = importlib.import_module("shelf.collectorprocess.tools.parse_tools")
config = importlib.import_module("shelf.collectorprocess.config")
collectorprocess = importlib.import_module("shelf.collectorprocess")

# get the location of the python source file (avoids errors when running script from other folders)
# PATH = os.path.dirname(os.path.abspath(__file__))


class BaseObject(object):
    pass


def start_flow(collectorName, q, baseObject, familyObj):
    try:
        op = FlowManager(collectorName, baseObject=baseObject)
        op.start(familyObj=familyObj, baseObject=baseObject)
        q.put(baseObject)
    except Exception as e:
        template = "An untreated exception of type '{0}' occurred due to '{1}'"
        message = template.format(type(e).__name__, e.args)
        logger.error(message, __file__)
        traceback.print_exc(file=sys.stderr)
        q.put(baseObject)


def launch_multi_processing(nSubProcesses, args, familyObjs, baseObject):
    sub_process_list = list()

    try:
        q = Queue()
        base_objects = list()

        for i in range(len(familyObjs)):
            new_process = Process(target=start_flow, args=(args.collectorName, q, baseObject, familyObjs[i]))
            sub_process_list.append(new_process)
            # By starting the process from the end of the list, it ensures a reference to it already exists in that list in case it needs to be terminated forcefully
            sub_process_list[-1].start()

        for p in sub_process_list:
            # The q.get() will wait until the first spawned process uses q.put() or exits.
            p.join()
            base_objects.append(q.get())

        for bo in base_objects:
            # Joins the results from all child processes
            baseObject.results.update(bo.results)

    except Exception as e:
        template = "An untreated exception of type '{0}' occurred due to '{1}'"
        message = template.format(type(e).__name__, e.args)
        logger.error(message, __file__)
        logger.toNA(str(e))
        traceback.print_exc(file=sys.stderr)

        logger.info("Terminating child processes.", __file__)

        for p in sub_process_list:
            p.terminate()
            p.join()


def parse_arguments():
    parser = argparse.ArgumentParser(description='Run an ETL (Extract, Transform and Load) task.')
    parser.add_argument('-d', '--debug', dest='debug', action='store_true', help='run in debug mode')
    parser.add_argument('collectorName', metavar='collectorName', type=str, help='name of collector to use')

    parser.add_argument('--vendor', help='Vendor', required=True)
    parser.add_argument('--model', help='Model', required=True)

    parser.add_argument("--hostname", help="mongodb server hostname")
    parser.add_argument("--username", help="mongodb enrichment db username")
    parser.add_argument("--password", help="mongodb enrichment db password")
    parser.add_argument("--port", help="mongodb enrichment db port")
    parser.add_argument("--instance", help="optional field defining the instance to run")
    parser.add_argument("--scope", help="optional field defining the instance to run. Overrides --instance")

    parser.add_argument("--conf", default=os.path.join(config.__path__[0], "config.json"), type=argparse.FileType('r'),
                        help='the configuration file')

    parser.add_argument("--kafkaParam", help="alternative to all the following parameters")

    parser.add_argument("--fetchTime", help="time of the data collection/creation", type=str)
    parser.add_argument("--sourceId", help="id of the source of the event, usually an IP", type=str)
    parser.add_argument("--hostId", help="name of the source host", type=str)
    parser.add_argument("--eventType", help="type of the event", type=str, default='COLLECT')
    parser.add_argument("--eventOriginId", help="name of service that originated the event", type=str)
    parser.add_argument("--parentEventId", help="id of the parent event", type=str)

    parser.add_argument("--collection", help="optional field defining the name of the collection to insert")
    parser.add_argument('input', metavar='input', type=pt.exists, nargs='?', default='', help='input (file or folder)')
    parser.add_argument('--out', metavar='output', type=pt.is_w_dir, help='optional output folder')

    parser.add_argument('--reprocessing', help='reprocessing', action="store_true", required=False)
    parser.add_argument('--selectedFamilies', type=str, default=None, required=False,
                        help='Comma separated list of families to reprocess')

    # Will exit the application if the conditions above are not satisfied
    args = parser.parse_args()

    return args


if __name__ == "__main__":

    # Base object initialization
    baseObject = BaseObject()

    # Parsing arguments stage---------------------------------------------------------
    try:
        args = parse_arguments()
    except argparse.ArgumentTypeError as e:
        logger.error("Could not validate arguments, due to {0}. Aborting execution.".format(e), __file__)
        sys.exit()

    if args.debug:
        logger.set_log_level("debug")
    if not args:
        baseObject.results.printResults()
        sys.exit()
    # --------------------------------------------------------------------------------

    # Configurations loaded from conf file
    configuration = json.load(args.conf)
    baseObject.folders = configuration["folders"]
    baseObject.operationSpecFilesName = configuration["operationSpecFilesName"]
    baseObject.operationBaseName = configuration["operationBaseName"]
    baseObject.kafkaConfigurationFileName = configuration["kafkaConfigurationFileName"]
    baseObject.kafkaReprocessConfigurationFileName = configuration["kafkaReprocessConfigurationFileName"]
    baseObject.mongoConfigurationFileName = configuration["mongoConfigurationFileName"]
    baseObject.mongoSNMPConfigurationFileName = configuration["mongoSNMPConfigurationFileName"]
    baseObject.mongoNAMFConfigurationFileName = configuration["mongoNAMFConfigurationFileName"]

    baseObject.args = args
    baseObject.results = Results()
    baseObject.vars = dict()

    # Transform all baseObject paths to absolute paths of the system
    projectDirectory = os.path.dirname(os.path.realpath(__file__))
    projectDirectory = collectorprocess.__path__[0]
    baseObject.absFolders = dict()
    for folderKey, folderName in baseObject.folders.items():
        baseObject.absFolders[folderKey] = os.path.join(projectDirectory, folderName)

    loadOperationSpec = SpecLoader.loadOperationSpec(operation=args.collectorName, instance=args.instance,
                                                     scope=args.scope, baseObject=baseObject)

    if loadOperationSpec is not False:

        try:
            op = FlowManager(args.collectorName, baseObject=baseObject)

            op.start(baseObject=baseObject)

            if hasattr(baseObject, "multi"):
                familyObject = baseObject.multi["familyObjects"][0]
                familyObjects = familyObject.splitObject(baseObject.multi["nSubProcesses"])
                nSubProcesses = baseObject.multi["nSubProcesses"]

                del baseObject.multi

                launch_multi_processing(nSubProcesses, args, familyObjects, baseObject)

        except Exception as e:
            template = "An untreated exception of type '{0}' occurred due to '{1}'"
            message = template.format(type(e).__name__, e.args)
            logger.error(message, __file__)
            traceback.print_exc(file=sys.stderr)

    baseObject.results.printResults()