#!/usr/bin/env python

__doc__ = \
    '''

'''

__version__ = '1.0'

__authors__ = [
    "Version 1.0: Joao Pio <joao-t-pio@alticelabs.com>"
]

from pysnmp.hlapi import *
import subprocess
import importlib

logger = importlib.import_module("shelf.collectorprocess.logger").logger


class SNMPConnector():

    # Class Constructor
    def __init__(self, port=161, baseObject={}):
        self._bulkLimit = 30
        self._timeout = 10
        self._retries = 3
        # Necessary for instances without port configuration
        self._default_port = port

        self.v3authentication_protocols = {"MD5": usmHMACMD5AuthProtocol, "SHA1": usmHMACSHAAuthProtocol, None: None}
        self.v3privacy_protocols = {"DES": usmDESPrivProtocol, "AES": usmAesCfb128Protocol, None: None}

        self._port = port
        self._version = 2

        if hasattr(baseObject, "snmp"):
            if "timeout" in baseObject.snmp:
                self.timeout = baseObject.snmp["timeout"]

            if "retries" in baseObject.snmp:
                self.retries = baseObject.snmp["retries"]

    def node_attributes_formatter(self, node):

        self.version_translate(node["versionSnmp"])

        # Clean all empty strings and turn them into NoneType
        for key in ["authProtocol", "authPassword", "privacyProtocol", "privacyPassword"]:
            try:
                if node[key] == "" or node[key] == " ":
                    node[key] = None
            except KeyError:
                # Attribute not present
                continue

        if self._version == 3:
            try:
                node["authProtocol"] = self.v3authentication_protocols[node["authProtocol"]]
                node["privacyProtocol"] = self.v3privacy_protocols[node["privacyProtocol"]]
            except KeyError as e:
                logger.error(
                    "Provided credentials not adequate for SNMP version {0}. {1}.".format(self._version, node),
                    __file__)
                raise ValueError

        return node

    def version_translate(self, version):
        if version in ["v1", "1"]:
            self._version = 1
        elif version in ["v2c", "v2", "2"]:
            self._version = 2
        elif version in ["v3", "3"]:
            self._version = 3

    @staticmethod
    def objectify_string_oid(oid):

        try:
            res = []

            for c in oid.split("."):
                res.append(int(c))
        except AttributeError:
            # oid is not a splittable string
            return None
        except ValueError:
            # component of split is not a number
            return None

        return tuple(res)

    @property
    def bulkLimit(self):
        return self._bulkLimit

    @bulkLimit.setter
    def bulkLimit(self, value):
        self._bulkLimit = value

    @property
    def timeout(self):
        return self._timeout

    @timeout.setter
    def timeout(self, value):
        self._timeout = value

    @property
    def retries(self):
        return self._retries

    @retries.setter
    def retries(self, value):
        self._retries = value

    """
    ####################################################################################################
    General methods (SNMP all versions)
    ####################################################################################################
    """

    """
        Function to build the appropriate authentication data according to the version.

        Credentials format for V3:
        {
            "sec_level": {noAuthNoPriv|authNoPriv|authPriv},
            "username": username,
            "auth_protocol": {MD5|SHA1},
            "auth_passphrase": authentication passphrase,
            "priv_protocol": {DES|AES},
            "priv_passphrase": pivacy passphrase,
            "context": database context
        }

        Credentials format for V1 and V2:
        {
            "community" : password
        }

        Returns:
            - CommunityData() for v1/v2
            - UsmUserData() for v3

    """

    def build_auth_data(self, credentials, version=2):

        if version == 3:
            try:
                auth_data = UsmUserData(
                    credentials["username"],
                    authProtocol=credentials["authProtocol"],
                    authKey=credentials["authPassword"],
                    privProtocol=credentials["privacyProtocol"],
                    privKey=credentials["privacyPassword"]
                )
            except KeyError as e:
                logger.error(
                    "Provided credentials not adequate for SNMP version {0}. {1}.".format(version, credentials),
                    __file__)
                return
        elif version == 1:
            if "community" not in credentials.keys():
                logger.error(
                    "Provided credentials not adequate for SNMP version {0}. {1}.".format(version, credentials),
                    __file__)
                return

            auth_data = CommunityData(credentials["community"], mpModel=0)
        else:
            if "community" not in credentials.keys():
                logger.error(
                    "Provided credentials not adequate for SNMP version {0}. {1}.".format(version, credentials),
                    __file__)
                return

            auth_data = CommunityData(credentials["community"])

        return auth_data

    """
        Function to check for equipment connectivity, compatible with all SNMP versions.
        Method used is an SNMP get to the most common OID in a SNMP client, the sysDescr

        Parameters:
            ip: The SNMP equipment IP address

        Optional:
            credentials:
                The necessary parameters to authenticate the request with the equipment as a dictionary.
                For version 1/2c:
                    - "community"
                For version 3:
                    - "username"
                    - "authProtocol"
                    - "authPassword"
                    - "privacyProtocol"
                    - "privacyPassword"
                    - "securityLevel" - Inferred by the presence or not of the previous parameters
                    - "context" - Not used

            version:
                The SNMP protocol version.
                Accepted values:
                    - 1, 2 or 3
                Default:
                    - 2

            port:
                The SNMP service port.
                Accepted values:
                    - any number
                Default:
                    - 161

            ping_oid:
                The OID to use as a SNMP "ping".
                Accepted values:
                    - String in the format of "1.X.X.X.X"

        Returns: Nothing

    """

    def check_snmp_connectivity(self, ip, credentials={}, ping_oid=None, version=2, port=161):

        self.version_translate(version)

        auth_data = self.build_auth_data(credentials, self._version)

        if ping_oid is None:
            object_ping_oid = ObjectType(ObjectIdentity('SNMPv2-MIB', 'sysDescr', 0))
        else:
            # Validate oid requested
            tupled_ping_oid = SNMPConnector.objectify_string_oid(ping_oid)

            if tupled_ping_oid is None:
                logger.error(
                    "Could not turn oid {0} into object. SNMP connectivity test failed.".format(ping_oid), __file__)
                raise ValueError

            object_ping_oid = ObjectType(ObjectIdentity(tupled_ping_oid))

        snmpEngine = SnmpEngine()

        if "context" in credentials:
            context = ContextData(contextName=str(credentials["context"]))
        else:
            context = ContextData()

        # Invoke the get command with the appropriate credentials
        for errorIndication, errorStatus, errorIndex, varBinds in getCmd(
                snmpEngine,
                auth_data,
                UdpTransportTarget((ip, port)),
                context,
                object_ping_oid,
                lookupMib=False
        ):

            if errorIndication:
                logger.warning("SNMP connectivity test failed. {0}. [{1}]".format(errorIndication, ip), __file__)
                raise IOError
            elif errorStatus:
                logger.warning("SNMP connectivity test failed. {0}. [{1}]".format(errorStatus.prettyPrint(), ip),
                               __file__)
                raise IOError

        logger.info("Connectivity to equipment {0} - {1} established".format(ip, varBinds[0][1].prettyPrint()),
                    __file__)

        return

    """
        Return a list of tuples (oid, value) of all the lexographic objects lower than the provided oid.
        Allows for filtering of the responses.

        Parameters:
            ip: The SNMP equipment IP address
            requested_oid: The desired OID from which to perform the walk

        Optional:
            credentials:
                The necessary parameters to authenticate the request with the equipment as a dictionary.
                For version 1/2c:
                    - "community"
                For version 3:
                    - "username"
                    - "authProtocol"
                    - "authPassword"
                    - "privacyProtocol"
                    - "privacyPassword"
                    - "securityLevel" - Inferred by the presence or not of the previous parameters
                    - "context" - Not used

            version:
                The SNMP protocol version.
                Accepted values:
                    - 1, 2 or 3
                Default:
                    - 2

            return_index_only:
                Flag to activate the return of the index portion of the OID ONLY.
                Accepted values:
                    - True/False
                Default:
                    - False

            port:
                The SNMP service port.
                Accepted values:
                    - any number
                Default:
                    - 161

            filters:
                The filters through which the returned entries might be filtered. Filtering modes include oid and value.

                    Ex1: {
                            "type": "oid",
                            "terms": [ "1.3.6.1.4.1.637.61.1.23.3.1.3.4362", "1.3.6.1.4.1.637.61.1.23.3.1.3.4363" ]
                        }

                    Ex2: {
                            "type": "value",
                            "terms": [ "ethernetCsmacd(6)", "6", "lvlan(135)", "135" ]
                        }
                Default:
                    - {}

        Returns:
            - list of tuples (oid, value)

    """

    # SNMP walk, either achieved through bulk_walk or get_next, depending on the version supplied
    def walk(self, ip, requested_oid, credentials={}, version=2, timeout=1, retries=0, error_tolerance=10, return_index_only=False, filters={}, port=161):

        self.version_translate(version)

        # Validate oid requested
        tupled_requested_oid = SNMPConnector.objectify_string_oid(requested_oid)

        if tupled_requested_oid is None:
            logger.error(
                "Could not turn oid {0} into object".format(requested_oid), __file__)
            return None

        object_requested_oid = ObjectType(ObjectIdentity(tupled_requested_oid))

        auth_data = self.build_auth_data(credentials, self._version)

        # Convert "terms" to a dict since it will be faster to verify if a term exists in a dict than a list
        if filters:
            filters["terms"] = {key: "" for key in filters["terms"]}

            if filters["type"] == "oid":
                filter_type = "oid"
            else:
                filter_type = "value"

        snmp_engine = SnmpEngine()

        if "context" in credentials:
            context = ContextData(contextName=str(credentials["context"]))
        else:
            context = ContextData()

        filtered_results = []
        errors = 0

        if self._version == 1:
            for errorIndication, errorStatus, errorIndex, varBinds in nextCmd(snmp_engine,
                                                                              auth_data,
                                                                              UdpTransportTarget((ip, port), timeout=timeout, retries=retries),
                                                                              context,
                                                                              object_requested_oid,
                                                                              lexicographicMode=False):

                if errorIndication is None:
                    # Successful response resets the error tolerance indicator
                    errors = 0

                    # logger.info("nextCmd {0}".format(varBinds[0]), __file__)

                    for entry in varBinds:
                        oid = str(entry[0])
                        val = entry[1].prettyPrint()

                        if return_index_only:
                            # Calculates which part of the oid is the index, and places it in the return variable
                            len_oid = len(object_requested_oid[0])
                            object_instance_oid = entry[0].getOid()
                            object_name_to_return = object_instance_oid[len_oid:]
                        else:
                            object_name_to_return = entry[0].getOid()

                        # If filters were provided
                        if filters:
                            if filter_type == "oid":
                                if oid in filters["terms"]:
                                    filtered_results.append((object_name_to_return, entry[1]))
                            else:
                                # Add entries that exist in the provided filters
                                if val in filters["terms"]:
                                    filtered_results.append((object_name_to_return, entry[1]))
                        else:
                            filtered_results.append((object_name_to_return, entry[1]))
                else:
                    logger.error(
                        "errorIndication {0}, errorStatus {1}, errorIndex {2}".format(errorIndication, errorStatus,
                                                                                      errorIndex, varBinds), __file__)
                    # Increase the error counter, and break off in case limit is reached
                    errors += 1
                    if errors > error_tolerance:
                        logger.error("Error tolerance of {0} was surpassed. Cancelling walk.".format(error_tolerance))
                        break
                    else:
                        continue
        else:

            for errorIndication, errorStatus, errorIndex, varBinds in bulkCmd(snmp_engine, auth_data,
                                                                              UdpTransportTarget((ip, port), timeout=timeout, retries=retries),
                                                                              context, 0, 25,
                                                                              object_requested_oid,
                                                                              ignoreNonIncreasingOid=True,
                                                                              lexicographicMode=False):

                if errorIndication is None:
                    # Successful response resets the error tolerance indicator
                    errors = 0

                    # logger.info("bulkCmd {0}".format(varBinds[0]), __file__)

                    for entry in varBinds:
                        oid = str(entry[0])
                        val = entry[1].prettyPrint()

                        if return_index_only:
                            # Calculates which part of the oid is the index, and places it in the return variable
                            len_oid = len(object_requested_oid[0])
                            object_instance_oid = entry[0].getOid()
                            object_name_to_return = object_instance_oid[len_oid:]
                        else:
                            object_name_to_return = entry[0].getOid()

                        # If filters were provided
                        if filters:
                            if filter_type == "oid":
                                if oid in filters["terms"]:
                                    filtered_results.append((object_name_to_return, entry[1]))
                            else:
                                # Add entries that exist in the provided filters
                                if val in filters["terms"]:
                                    filtered_results.append((object_name_to_return, entry[1]))
                        else:
                            filtered_results.append((object_name_to_return, entry[1]))
                else:
                    logger.error(
                        "errorIndication {0}, errorStatus {1}, errorIndex {2}".format(errorIndication, errorStatus,
                                                                                      errorIndex, varBinds), __file__)
                    # Increase the error counter, and break off in case limit is reached
                    errors += 1
                    if errors > error_tolerance:
                        logger.error("Error tolerance of {0} was surpassed. Cancelling walk.".format(error_tolerance))
                        break
                    else:
                        continue

        return filtered_results

    """
    ####################################################################################################
    SNMP V2 compatible methods
    ####################################################################################################
    """

    """
            Return a list of tuples (oid, value) of all the lexographic objects lower than the provided oid.

            REQUIRED:

            ip: Target equipment
            community: Community string
            requested_oid: The desired OID to start the subprocess_walk_v2

            OPTIONAL:

            return_index_only: Remove the part of the OID that is not the index, when returning results. Default is False

            filters:

            The returned entries might be filtered by oid or value

            Ex1:
                {
                    "type": "oid",
                    "terms": [ "1.3.6.1.4.1.637.61.1.23.3.1.3.4362", "1.3.6.1.4.1.637.61.1.23.3.1.3.4363" ]
                }

            Ex2:
                {
                    "type": "value",
                    "terms": [ "ethernetCsmacd(6)", "6", "lvlan(135)", "135" ]
                }

            port: The port used by the SNMP protocol in the target equipment. Default is 161

    """

    def subprocess_walk_v2(self, ip, community, requested_oid, return_index_only=False, filters={}, port=161):

        if self._port:
            port = self._port

        result = list()

        # Convert "terms" to a dict since it will be faster to verify if a term exists in a dict than a list
        if filters:
            filters["terms"] = {key: "" for key in filters["terms"]}

        for oid, value in self.__bulk_walk(ip, community, requested_oid, port):

            oid_to_return = oid

            # Check No Such Instance and No Such Object in order not to return this result
            if "NO SUCH INSTANCE" in value.upper() or "NO SUCH OBJECT" in value.upper():
                continue

            # Shorten OID to index if requested by parameter
            if return_index_only is True:
                oid_to_return = oid[len(requested_oid):].strip(".")

            if filters:
                if filters["type"] == "oid":
                    if oid in filters["terms"]:
                        result.append((oid_to_return, value))
                elif filters["type"] == "value":
                    if value in filters["terms"]:
                        result.append((oid_to_return, value))
            else:
                result.append((oid_to_return, value))

        return result

    # Calls a subprocess from the OS
    def __bulk_walk(self, ip, community, oid, port=161):

        if self._port:
            port = self._port

        proc = subprocess.Popen(
            ["snmpbulkwalk", "-v2c", "-t", str(self.timeout), "-r", str(self.retries), "-Onq", "-c", community,
             "{0}:{1}".format(ip, port), oid], stdout=subprocess.PIPE)

        for line in iter(proc.stdout.readline, ''):
            try:
                # Split line by first space to get oid and value
                result_oid, value = line.split(" ", 1)
                result_oid = result_oid.strip(".")
                value = value.strip()

                yield result_oid, value

            except ValueError, e:

                # Buffer has finished
                logger.warning("{0} on {1}".format(e, ip))
                continue