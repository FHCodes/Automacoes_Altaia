#!/usr/bin/env python

__doc__ = \
    '''

'''
__version__ = '0.5'

__authors__ = [
    "Version 0.5: Joao Pio <joao-t-pio@alticelabs.pt>"
]

# Native libraries
import importlib
import os
import re
import uuid
import json

from schema import Schema, Use, Regex, Optional
from datetime import datetime, date
from confluent_kafka import Producer
import pytz

# Local libraries
BaseOperator = importlib.import_module("shelf.collectorprocess.operators.BaseOperator").BaseOperator
FamilyObject = importlib.import_module("shelf.collectorprocess.operators.FamilyObject").FamilyObject
logger = importlib.import_module("shelf.collectorprocess.logger").logger


class DateTimeEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime) or isinstance(o, date):
            return o.isoformat()

        return json.JSONEncoder.default(self, o)


class MediationProducer(object):

    def __init__(self, bootstrap_servers, **extra_configs):

        conf = extra_configs
        conf['bootstrap.servers'] = bootstrap_servers
        # Set the message behavior on delivert of an event
        conf['on_delivery'] = self._on_delivery
        # Set the error handling function
        conf['error_cb'] = self.error_cb
        # Suppress librdkafka internal logs
        conf['log_level'] = 0

        self.connection_retries = 3
        self.connection_error_regex = re.compile(r"(Failed to resolve|brokers are down)")

        self._producer = Producer(**conf)

    @staticmethod
    def _on_delivery(err, msg):
        if err is not None:
            logger.error(("Message '{0}' could not be delivered on topic '{1}' due to '{2}'".format(msg.value(), msg.topic(), err.str())), __file__)
        else:
            pass
            # print "Message '{0}' delivered to topic '{1}'".format(msg.value(), msg.topic())
            # print "{0},".format(msg.value())

    def __enter__(self, *args):
        self._producer.poll(0)
        return self

    def __exit__(self, *args):
        self._producer.flush()

    def send(self, topic, message):
        self._producer.produce(topic, json.dumps(message, cls=DateTimeEncoder))

    def error_cb(self, err):
        # Find out if brokers are not responding
        if self.connection_error_regex.search(err.str()) is None:
            logger.error("{0}".format(err.str()),
                         __file__)
        # Silently decrement retries for connection errors
        elif self.connection_retries > 0:
            self.connection_retries -= 1


class Operator(BaseOperator):

    # Class Constructor
    def __init__(self, operationParams, baseObject={}):
        BaseOperator.__init__(self, operationParams, baseObject=baseObject)
        self.pid = os.getpid()

        # Events counter
        self.ev_counter = 0

        # Get kafka configurations from file
        if baseObject.args.reprocessing:
            kafka_conf = os.path.join(baseObject.absFolders["config"], baseObject.kafkaReprocessConfigurationFileName)
        else:
            kafka_conf = os.path.join(baseObject.absFolders["config"], baseObject.kafkaConfigurationFileName)

        try:
            with open(kafka_conf) as f:
                kafka_conf = json.load(f)
        except ValueError as e:
            logger.error("Could not load kafka configuration file. Unrecognized json format at {0}".format(kafka_conf), __file__)
            # Cancel FlowManager.buildOperationsQueue
            raise ValueError()
        except IOError as e:
            logger.error("Could not load kafka configuration file. Expected location: {0}".format(kafka_conf), __file__)
            # Cancel FlowManager.buildOperationsQueue
            raise IOError()

        # self.evProducer = MediationProducer(",".join(kafka_conf["broker_list"]),
        self.evProducer = MediationProducer(kafka_conf["broker_list"],
                                            **kafka_conf["extra_configs"])

        self.evTopic = kafka_conf["topic"]

        r'''
        self._ip_regex = re.compile(
            r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$')
        self._hostname_regex = re.compile(
            r'^(?=.{1,253}$)(?!-)[a-zA-Z0-9-]{1,63}(?<!-)(\.(?!-)[a-zA-Z0-9-]{1,63}(?<!-))*$')
        '''

        self.schema = Schema(
            {
                'mediationEnvelope':
                    {
                        'fetchTime': Regex(
                            r'^(19|20)[0-9]{2}-(1[0-2]|0[1-9])-(3[0-1]|0[1-9]|[1-2][0-9])T(2[0-3]|[0-1][0-9]):[0-5][0-9]:[0-5][0-9](\.[0-9]+)?(Z|[+-](2[0-3]|[0-1][0-9]):([0-5][0-9]))$'),
                        'sourceId': Use(str),  # lambda source_id: self._ip_regex.match(source_id) or self._hostname_regex.match(source_id)
                        'hostId': Use(str),
                        Optional('selectedFamilies'): Use(str)
                    },
                'eventType': Use(str),
                'eventOriginId': Use(str),
                # 'eventCreationTime' : Regex(r'^(19|20)[0-9]{2}-(1[0-2]|0[1-9])-(3[0-1]|0[1-9]|[1-2][0-9])T(2[0-3]|[0-1][0-9]):[0-5][0-9]:[0-5][0-9](\.[0-9]+)?(Z|[+-](2[0-3]|[0-1][0-9])([0-5][0-9]))$'),
                'parentEventId': Use(str)
            })

    @staticmethod
    def extract_kafka_params(args):

        extracted_params = dict()
        extracted_params["mediationEnvelope"] = dict()

        # Check if kafkaParams was provided:
        try:
            kafka_params = args.kafkaParam
        except AttributeError:
            kafka_params = None

        # Parse the kafkaParams argument
        if kafka_params is not None:
            try:
                firstmatch = re.match("^mediationEnvelope{(.*)}(.*)$", kafka_params)

                if firstmatch:
                    # mediationEnvelope section
                    segments = firstmatch.group(1).split("#")

                    for seg in segments:
                        seg_match = re.match("^(.*)=(.*)$", seg)

                        if seg_match:
                            extracted_params["mediationEnvelope"][seg_match.group(1)] = seg_match.group(2)
                        # Invalid field, moves to next one
                        else:
                            continue

                    # prerouting envelope section
                    segments = firstmatch.group(2).split("#")

                    for seg in segments:
                        seg_match = re.match("^(.*)=(.*)$", seg)

                        if seg_match:
                            extracted_params[seg_match.group(1)] = seg_match.group(2)
                        # Invalid field, moves to next one
                        else:
                            continue
                else:
                    logger.error(
                        "Failed to extract the parameters for the Kafka becauseformat was wrong", __file__)
                    return None

                return extracted_params

            except Exception as e:
                logger.error(
                    "Failed to extract the parameters for the Kafka producer due to {0}".format(e), __file__)
                return None
        else:
            try:
                extracted_params["eventOriginId"] = args.eventOriginId
                extracted_params["eventType"] = args.eventType
                extracted_params["parentEventId"] = args.parentEventId

                extracted_params["mediationEnvelope"]["fetchTime"] = args.fetchTime
                extracted_params["mediationEnvelope"]["hostId"] = args.hostId
                extracted_params["mediationEnvelope"]["sourceId"] = args.sourceId

                if args.selectedFamilies:
                    extracted_params["mediationEnvelope"]["selectedFamilies"] = args.selectedFamilies

                return extracted_params
            except AttributeError as e:
                logger.error(
                    "There is a parameter missing to build message envelope: {0}".format(e), __file__)
                return None

    def process(self, familyObj=FamilyObject(), baseObject={}):

        # get unitId
        unit_id = familyObj.getUnitID()
        file_name = familyObj.fileName

        # Obtain kafkaParam (format should be field=data#field=data#field=data... or the separated arguments
        ext_params = self.extract_kafka_params(baseObject.args)

        try:
            ext_params = self.schema.validate(ext_params)
        except Exception as e:
            logger.error("KafkaParameters not correct due to {0}".format(e), __file__)
            raise e

        ext_params["mediationEnvelope"]["familyId"] = unit_id

        try:
            ext_params["mediationEnvelope"]["dataTypeId"] = "{0}/{1}/{2}".format(
                baseObject.args.vendor,
                baseObject.args.model,
                unit_id)
        except KeyError as e:
            logger.error("Could not build dataTypeId due to {0}".format(e), __file__)
            raise e

        ext_params["correlationId"] = file_name
        
        # # Se a flag 'print' estiver ativada, abra o arquivo UMA vez (modo utf-8)
        if "print" in self._options:
            arquivo = open('saida.json', 'a')
        #-------------------------------------------------------------
        # Evoking the event producer this way, guarantees an automatic flush (__exit__) at he the end
        with self.evProducer as prod:

            for doc in familyObj.getDocuments():
                # generate UUID for this event
                # ext_params["eventId"] = str(uuid.uuid4())
                ext_params["eventId"] = "teste"
            #    ext_params["eventCreationTime"] = datetime.now(pytz.UTC).isoformat()
                ext_params["eventCreationTime"] = "2018-03-05T11:52:28.426+00:00"
                ext_params["mediationEnvelope"]["data"] = doc["data"]
                ext_params["mediationEnvelope"]["dataTime"] = doc["dataTime"]
                ext_params["mediationEnvelope"]["granularitySec"] = doc["granularitySec"]
                
                try:
                    if "print" in self._options.keys():
                        import copy
                        ext_params_toprint = copy.deepcopy(ext_params)
        
                        if "excludes" in self._options.keys():
                            for param in ext_params["mediationEnvelope"]["data"]:
                                if param in self._options["excludes"].split(";"):
                                    ext_params_toprint["mediationEnvelope"]["data"].pop(param)
        
                        import collections
                        od = collections.OrderedDict(sorted(ext_params_toprint["mediationEnvelope"]["data"].items()))
        
                        ext_params_toprint["mediationEnvelope"].pop("data")
                        ext_params_toprint["mediationEnvelope"]["data"] = od
                        
                        #3) grava um JSON por linha
                        json.dump(ext_params_toprint, arquivo, ensure_ascii=False)
                        arquivo.write('\n')
                        
                        # print ext_params_toprint
                        
                    else:
                        prod.send(self.evTopic, ext_params)
    
                    # increase events counter
                    self.ev_counter += 1

                except Exception as e:
                    logger.error("Producer.send ERROR {0}".format(e), __file__)
                    raise e

        self.nextOp(familyObj=familyObj, baseObject=baseObject)

    def finish(self, familyObj=None, baseObject={}):

        # Set result values
        duration = datetime.now() - baseObject.results.startTime

        duration_in_seconds = duration.seconds + duration.microseconds / float(1000000)

        events_per_sec = float("{0:.0f}".format(self.ev_counter / duration_in_seconds))

        # Main process does not process files
        if self.ev_counter != 0:
            baseObject.results.addResult(label="TOTAL EVENTS", value=self.ev_counter)
            baseObject.results.addResult(label="EVENTS", value=self.ev_counter, pid=self.pid)
            baseObject.results.addResult(label="DURATION".format(self.pid), value=duration_in_seconds, pid=self.pid, unit="secs")
            baseObject.results.addResult(label="PERFORMANCE".format(self.pid), value=events_per_sec, pid=self.pid, unit="events/sec")
