#!/usr/bin/env python3

__doc__ = \
    '''
    This object is the vehicle for passing data between operations
'''

__version__ = '0.2'

import os
import sys
from datetime import datetime
import importlib

# Local libraries
logger = importlib.import_module("shelf.collectorprocess.logger").logger


class Results(object):

    # Class Constructor
    def __init__(self):

        self._startTime = datetime.now()

        self._nDocsOut = 0
        self._nFilesIn = 0
        self._nFilesSuccess = 0

        self._nameJust = 30
        self._valueJust = 9
        self._dateJust = 24 + self._valueJust - 6
        self._performanceJust = 27

        self.printScriptInit()

        self._resultsList = list()
        self._subprocess_results = dict()

    @property
    def startTime(self):
        return self._startTime

    @startTime.setter
    def startTime(self, value):
        self._startTime = value

    @property
    def resultsList(self):
        return self._resultsList

    @resultsList.setter
    def resultsList(self, value):
        self._resultsList = value

    @property
    def subprocess_results(self):
        return self._subprocess_results

    @subprocess_results.setter
    def subprocess_results(self, value):
        self._subprocess_results = value

    @property
    def nameJust(self):
        return self._nameJust

    @nameJust.setter
    def nameJust(self, value):
        self._nameJust = value

    @property
    def valueJust(self):
        return self._valueJust

    @valueJust.setter
    def valueJust(self, value):
        self._valueJust = value

    @property
    def dateJust(self):
        return self._dateJust

    @dateJust.setter
    def dateJust(self, value):
        self._dateJust = value

    def update(self, results):

        for res in results.resultsList:
            here = False

            for selfRes in self.resultsList:

                if selfRes["label"] == res["label"]:

                    here = True

                    if res["label"] in ["TOTAL FILES"]:
                        continue
                    elif "TOTAL" in res["label"] or res["label"] == "WRITTEN LINES":
                        selfRes["value"] += res["value"]
                    else:
                        selfRes["value"] = (selfRes["value"] + res["value"]) / 2

            if not here:
                self.addResult(label=res["label"], value=res["value"], unit=res["unit"])

        for pid in results.subprocess_results:
            for res in results.subprocess_results[pid]:
                self.addResult(label=res["label"], value=res["value"], unit=res["unit"], pid=pid)

    def addResult(self, label="", value="", unit="", pid=""):
        try:
            pid = int(pid)
        # Comes without a pid, so it's not a subprocess value
        except ValueError:
            self.resultsList.append({
                "label": label,
                "value": value,
                "unit": unit
            })
            return

        if str(pid) in self.subprocess_results.keys():
            self.subprocess_results[str(pid)].append({
                "label": label,
                "value": value,
                "unit": unit
            })
        else:
            self.subprocess_results[str(pid)] = [{
                "label": label,
                "value": value,
                "unit": unit
            }]

    def printScriptInit(self):
        logger.printline('--------- {0}-----> {1} ---------'.format('SCRIPT START'.ljust(self.nameJust),
                                                                    self.startTime.strftime(
                                                                        "%d-%m-%y %H:%M:%S.%f").ljust(self.dateJust)))

    def printResults(self):

        end_time = datetime.now()

        # Set result values
        duration = end_time - self.startTime
        duration_in_seconds = duration.seconds + duration.microseconds / 1000000.0
        duration_str = "{0:.2f}".format(duration_in_seconds)

        self.addResult(label="TOTAL DURATION", value=duration_str, unit="secs")

        for res in self.resultsList:
            if res["label"] in ["TOTAL EVENTS"]:
                performance = float(res["value"]) / duration_in_seconds
                self.addResult(label="TOTAL PERFORMANCE", value="{0:.2f}".format(performance), unit="events/sec")

        if len(sys.argv) > 1 and os.path.exists("statisticsFile_" + sys.argv[1] + ".txt"):
            with open("statisticsFile_" + sys.argv[1] + ".txt", 'r') as statistics:
                stats_data = statistics.readlines()

        for pid in self.subprocess_results.keys():

            for res in self.subprocess_results[pid]:
                if isinstance(res["value"], float):
                    res["value"] = " {0:.2f}".format(float(res["value"]))

        stats = {}

        for res in self.resultsList:
            if isinstance(res["value"], float):
                res["value"] = "{0:.2f}".format(float(res["value"]))
            stats.update({res["label"]: res["value"]})

        if "TOTAL EVENTS" not in stats:
            stats["TOTAL EVENTS"] = 0
        if "TOTAL DURATION" not in stats:
            stats["TOTAL DURATION"] = 0
        if "TOTAL PERFORMANCE" not in stats:
            stats["TOTAL PERFORMANCE"] = 0

        str1 = "{0} EVENTS IN {1}s".format(stats["TOTAL EVENTS"], stats["TOTAL DURATION"])
        str2 = "{0} events/s".format(stats["TOTAL PERFORMANCE"])
        logger.printline('--------- {0}-----> {1} ---------'.format(str1.ljust(self.nameJust), str2.ljust(self._performanceJust)))

        logger.printline('--------- {0}-----> {1} ---------'.format('SCRIPT END'.ljust(self.nameJust),
                                                                    end_time.strftime("%d-%m-%y %H:%M:%S.%f").ljust(
                                                                        self.dateJust)))