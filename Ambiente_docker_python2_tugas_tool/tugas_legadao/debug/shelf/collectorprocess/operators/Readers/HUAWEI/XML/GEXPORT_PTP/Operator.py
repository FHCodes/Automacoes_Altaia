__doc__ = \
    '''
	Parser for HUAWEI Parameters GExport XML using sax
'''

__version__ = '0.1'

__authors__ = [
    "Version 1.0: Bruno Silva <bruno-e-silva@alticelabs.com>"
]

import io, re, os, json
import gzip
import copy
import HierarchyManager
from lxml import etree
import importlib
from datetime import datetime
from collections import OrderedDict

# Local libraries
BaseOperator = importlib.import_module("shelf.collectorprocess.operators.BaseOperator").BaseOperator
FamilyObject = importlib.import_module("shelf.collectorprocess.operators.FamilyObject").FamilyObject
logger = importlib.import_module("shelf.collectorprocess.logger").logger
mongoCon = importlib.import_module(
    "shelf.collectorprocess.operators.OutputManagers.Mongo.Operator").mongoConnection


class CellObject():

    def __init__(self, cell_id, cell_name, ci_or_localcellid, site_id, site_name, controller_name, tech):
        self._cell_id = cell_id
        self._cell_name = cell_name
        self._site_id = site_id
        self._site_name = site_name
        self._controller_name = controller_name
        self._tech = tech
        self._ci_or_localcellid = ci_or_localcellid

    def get_ci_or_localcellid(self):
        return self._ci_or_localcellid

    def set_ci_or_localcellid(self, value):
        self._ci_or_localcellid = value

    def get_cell_id(self):
        return self._cell_id

    def set_cell_id(self, value):
        self._cell_id = value

    def get_cell_name(self):
        if self._cell_name:
            return {"CELL_NAME": self._cell_name}
        return None

    def set_cell_name(self, value):
        self._cell_name = value

    def get_site_id(self):
        return self._site_id

    def set_site_id(self, value):
        self._site_id = value

    def get_site_name(self):
        if self._site_name:
            if self._tech == '2G':
                return {"BTS_NAME": self._site_name}
            elif self._tech == '3G':
                return {"NODEB_NAME": self._site_name}
            elif self._tech == '4G':
                return {"ENODEB_NAME": self._site_name}
            elif self._tech == '5G':
                return {"GNODEB_NAME": self._site_name}
        return None

    def set_site_name(self, value):
        self._site_name = value

    def get_controller_name(self):
        if self._controller_name:
            if self._tech == '2G':
                return {"BSC_NAME": self._controller_name}
            elif self._tech == '3G':
                return {"RNC_NAME": self._controller_name}
        return None

    def set_controller_name(self, value):
        self._controller_name = value


class SiteObject():

    def __init__(self, site_id, site_name, controller_name, tech):
        self._site_name = site_name
        self._site_id = site_id
        self._controller_name = controller_name
        self._tech = tech

    def get_site_id(self):
        return self._site_id

    def set_site_id(self, value):
        self._site_id = value

    def get_site_name(self):
        if self._site_name:
            if self._tech == '2G':
                return {"BTS_NAME": self._site_name}
            elif self._tech == '3G':
                return {"NODEB_NAME": self._site_name}
            elif self._tech == '4G':
                return {"ENODEB_NAME": self._site_name}
            elif self._tech == '5G':
                return {"GNODEB_NAME": self._site_name}
        return None

    def set_site_name(self, value):
        self._site_name = value

    def get_controller_name(self):
        if self._controller_name:
            if self._tech == '2G':
                return {"BSC_NAME": self._controller_name}
            elif self._tech == '3G':
                return {"RNC_NAME": self._controller_name}
        return None

    def set_controller_name(self, value):
        self._controller_name = value


class Operator(BaseOperator):

    def __init__(self, operationParams, baseObject={}):
        baseObject.enrich_cell_dict = dict()
        baseObject.enrich_localcell_dict = dict()
        baseObject.enrich_site_dict = dict()
        baseObject.enrich_controller_dict = dict()

        BaseOperator.__init__(self, operationParams, baseObject=baseObject)
        config = json.load(open('/opt/alticelabs/namf/src/shelf/collectorprocess/config/mongo_enrich_config.json'))
        config.update(
            json.load(open('{0}/{1}/config.json'.format(config['location'], self.options['enrich'].replace('.', '/')))))
        self._mongoConnection = mongoCon(config)
        self._mongoConnection.getConnection()
        self._enrichMapping = ['CELLNAME', 'CELL_NAME', 'FDN', 'LOCELL', 'NODEBNAME', 'NODEB_NAME']

    def process(self, familyObj=FamilyObject(), baseObject={}):
        logger.debug("[Reader] Reading HUAWEI Parameters GExport XML files' contents...")

        filePath = familyObj.getFiles()[0]
        familyObj.clearFiles()

        fileName = os.path.basename(filePath)
        familyObj.fileName = fileName

        try:
            # If file is compressed, replace the file path with a gzip buffered stream
            try:
                match = re.match('GExport_(?P<elementName>.+?)_(?P<ip>[^_]+)_(?P<dateTime>\d{10})\d{4}\.xml.*',
                                 familyObj.fileName)
                if filePath.endswith('.gz'):
                    baseObject = self.enrichData(gzip.open(filePath), match.group('elementName'), baseObject)
                    modelsMapping = json.load(open(
                        '/opt/alticelabs/namf/src/shelf/collectorprocess/operators/Readers/HUAWEI/XML/GEXPORT_PTP/modelsMapping.json'))
                    self.fast_iter(gzip.open(filePath), familyObj, baseObject, modelsMapping, match)
                else:
                    baseObject = self.enrichData(filePath, match.group('elementName'), baseObject)
                    modelsMapping = json.load(open(
                        '/opt/alticelabs/namf/src/shelf/collectorprocess/operators/Readers/HUAWEI/XML/GEXPORT_PTP/modelsMapping.json'))
                    self.fast_iter(filePath, familyObj, baseObject, modelsMapping, match)
            except etree.ParseError:
                logger.warning("EMPTY XML file '{0}'".format(filePath))
        except IOError:
            logger.warning("Could not open sample file \"{}\" in read mode: ".format(filePath), __file__)

    def fast_iter(self, f, familyObj, baseObject, modelsMapping, match):
        context = iter(etree.iterparse(f, events=('start', 'end'), tag=('configData', 'class', 'object', 'parameter')))
        hm = HierarchyManager.HierarchyManager()

        # blacklist = ['2GHASHKEY' ,'2GUSERIDANONSWITCH' ,'3GHASHKEY' ,'3GUSERIDANONSWITCH' ,'ABISE1T1' ,'ACALGO' ,'ACDCVLIMIT' ,'ADMCTRL' ,'AISSCFG' ,'AITFOTHPARA' ,'AITFREV' ,'ALDPWRSW' ,'ALMBLKPARA' ,'ALMBLKSW' ,'ALMCAPACITY' ,'ALMCURCFG' ,'ALMFILTER' ,'ALMLVL' ,'ALMML' ,'ALMOBJMASKCFG' ,'ALMOSCISW' ,'ALMOSCITHRD' ,'ALMPORT' ,'ALMSCRN' ,'ALMSHLD' ,'AMRC' ,'AMRCWB' ,'ANTENNAPORT' ,'APPLICATION' ,'ATESTPARA' ,'BAMIPRT' ,'BATATPA' ,'BATCTPA' ,'BATTERY' ,'BBP' ,'BBUFAN' ,'BCFCVOLTAGE' ,'BEDLPWRDIFF' ,'BERTHRESHOLD' ,'BFDPROTOSW' ,'BOXRPT' ,'BRD' ,'BRDADMINSTATE' ,'BRDHSUPA' ,'BRDRESASSIGNMENT' ,'BRDSTALMSHLD' ,'BSC6900EQUIPMENT' ,'BSC6900GSMFUNCTION' ,'BSC6900UMTSFUNCTION' ,'BSC6910EQUIPMENT' ,'BSC6910GSMFUNCTION' ,'BSC6910UMTSFUNCTION' ,'BSCAISS' ,'BSCFCPARA' ,'BSCINNSOFT' ,'BSCINNTMR' ,'BSCJBF' ,'BSCNSPARA' ,'BSCPCUTYPE' ,'BSCPSGBPARA' ,'BSCPSINNERSOFTPARA' ,'BSCPSSTAT' ,'BSCPSTCDSCPMAP' ,'BSCPSUMPARA' ,'BSCSIGTRC' ,'BSCSTATATTR' ,'BSCTESTPARA' ,'BSCTMR' ,'BSCUDBO' ,'BSSGPPARA' ,'BSSLS' ,'BTSALMFLASHTHD' ,'BTSALMFLASHTW' ,'BTSBRDCAP' ,'BTSCELLPATCHPARA' ,'BTSPWRSHARE' ,'BTSPWRTYPE' ,'BTSRSTINFOEFFECT' ,'BTSRSTLIST' ,'CAB' ,'CALLBTSTRACE' ,'CALLSHOCKCTRL' ,'CAPARATERANGE' ,'CASCADEPORT' ,'CBSADDR' ,'CBSIUBCITFTIMER' ,'CCGN' ,'CDRFILE' ,'CELLAUTOHOMING' ,'CELLCBSDRX' ,'CELLDSACMANUALPARA' ,'CELLEFACH' ,'CELLFRC' ,'CELLHSDPCCH' ,'CELLLDB' ,'CELLLICENSE' ,'CELLMBDRINTERRAT' ,'CELLNFREQPRIOINFO' ,'CELLPUC' ,'CELLQUALITYMEAS' ,'CELLREDIRECTION' ,'CELLRLACTTIME' ,'CELLU2LTEHONCOV' ,'CERRMTIMER' ,'CHGTHRSHOLD' ,'CHK' ,'CHRLEVEL' ,'CHRRNCCTRL' ,'CHRSCOPECTRL' ,'CHRSW' ,'CIDCHG' ,'CLK' ,'CLKMODE' ,'CLKSRC' ,'CLSPATIMER' ,'CNTCHK' ,'CONFIGURE' ,'CONNTYPE' ,'CORRMPARA' ,'CPRIPORT' ,'CPSWITCH' ,'CPU' ,'CPUTHD' ,'CSABISCONGCTRL' ,'CSPRECTRL' ,'CTCH' ,'CTFTST' ,'CTRLFACTOR' ,'CTRLPLNFCPARA' ,'CTRLPLNSHAREPARA' ,'DCHTHDRATERATIO' ,'DELAYCLASS' ,'DELAYUPDATE' ,'DESENS' ,'DEVRSVDPARA' ,'DEVSOFTPARA' ,'DHCPSW' ,'DISTANCEREDIRECTION' ,'DLGROUP' ,'DPB' ,'DRD' ,'DRDMIMO' ,'DSACAUTOALGO' ,'DSP' ,'DSPLVDSMODE' ,'DSSPARA' ,'DTXDRXPARA' ,'E1T1BER' ,'E1T1WM' ,'E1T1WORKMODE' ,'E2EQOSPARA' ,'EDCHTHDRATERATIO' ,'EDCHTTIRECFG' ,'EMSTZ' ,'ENERGYCON' ,'ENVALMPARA' ,'EQMTOINVENTORYUNITHW' ,'ERACHBASIC' ,'ETHSWITCH' ,'EVENTCHRCTRL' ,'FACFG' ,'FACHBANDWIDTH' ,'FACHDYNTFS' ,'FACHLOCH' ,'FACHSCHEPRIO' ,'FANALMSW' ,'FANSPEED' ,'FCCOMMPARA' ,'FCCPUTHD' ,'FCMSGQTHD' ,'FCSW' ,'FDPCHPARA' ,'FDPCHRLPWR' ,'FLTCORRENABLECFG' ,'FMABUSYRULE' ,'FPMUX' ,'FRAMEMODE' ,'FRMHANDPRIO' ,'FTPCLT' ,'FTPCLTPORT' ,'FTPSCLT' ,'FTPSCLTDPORT' ,'FTPSRVSPD' ,'FTPSSRV' ,'GAFCALMPARA' ,'GALLCELLBLKSTAT' ,'GBSCREDGRP' ,'GCELLBTSSOFT' ,'GCELLBTSSOFTPARA' ,'GCELLFREQSCAN' ,'GCELLIBCAII' ,'GCELLINNHOBASI' ,'GCELLINNSOFT' ,'GCELLINNTMR' ,'GCELLMAIOPLAN' ,'GCELLOPTREV' ,'GCELLPSABISPARA' ,'GCELLRESELECTUTRANTDD' ,'GCELLRSVPARA' ,'GCELLSTATOPTPARA' ,'GCELLTA' ,'GCELLTEMPLATEPARA' ,'GCELLTRANPARA' ,'GCELLUNDPARA' ,'GCELLVAMOSPWR' ,'GCNCFGALMTHD' ,'GCNOPERATORREV' ,'GCSCHRCTRL' ,'GCSFILE' ,'GFORCESWITCH' ,'GHOSTSTATUS' ,'GKPIALMTHD' ,'GMMCSCHRCTRL' ,'GMMCSCHRSCOPE' ,'GMMMRCTRL' ,'GMMMRSCOPE' ,'GMMPSCHRCTRL' ,'GMMPSCHRSCOPE' ,'GMRCTRL' ,'GMRSCOPE' ,'GMSSAICCAP' ,'GNETAWARENESS' ,'GNODEREDCFGCTRL' ,'GNODEREDUNDANCY' ,'GPSCHRCTRL' ,'GPSDELAY' ,'GPSKPIALMTHD' ,'GREDGRPHOSTPOLICY' ,'GRSVPARA' ,'GSMCELL' ,'GSMNCELL' ,'GTMU' ,'GTRXRLALM' ,'GTRXRSVPARA' ,'HCSHO' ,'HOSTLOGSPD' ,'HSDPAFLOWCTRLPARA' ,'HSDPCCH' ,'HSSCCHLESSOPPARA' ,'HTCDPA' ,'HTPROTECT' ,'HWFACFG' ,'HWVER' ,'IFOFFSET' ,'IMBDYNTFS' ,'IMBFACH' ,'IMBSEMISTATICTF' ,'IMBSWITCH' ,'IMEITAC' ,'INFBRDRESCFG' ,'INGCHKTSK' ,'INNSOFTPARA' ,'INTBRDPARA' ,'INTERFREQHONCOV' ,'INTERRATHONCOV' ,'INVENTORYANTENNA' ,'INVENTORYBOARD' ,'INVENTORYBTSANTENNA' ,'INVENTORYBTSBOARD' ,'INVENTORYBTSFRAME' ,'INVENTORYBTSHOSTVER' ,'INVENTORYBTSRACK' ,'INVENTORYBTSSLOT' ,'INVENTORYFRAME' ,'INVENTORYHOSTVER' ,'INVENTORYPORT' ,'INVENTORYRACK' ,'INVENTORYSLOT' ,'INVENTORYUNITHW' ,'IPCHK' ,'ITELSHUTDOWN' ,'ITWKPIALMTHD' ,'IUBTRIGHOPARA' ,'IUTIMERANDNUM' ,'KPIALMTHD' ,'KPISELFCUREPARA' ,'L2L3ROUTEPOLICY' ,'LAPDLINK' ,'LCPSW' ,'LDM' ,'LDR' ,'LICALMTHD' ,'LICPARA' ,'LINECLK' ,'LLDPGLOBAL' ,'LLDPGLOBALINFO' ,'LNKSRC' ,'LOADTLIMIT' ,'LOCALETHPORT' ,'LOCALIP' ,'LOCALWAP' ,'LOCELLPRI' ,'LOCHPRIO' ,'LODCTRL' ,'LOGLIMIT' ,'LOGPARA' ,'LTECELL' ,'LTENCELL' ,'MAINSALARMBIND' ,'MANRESALMRPT' ,'MAXDSPFLTNUM' ,'MBMSALARMPARA' ,'MBMSFACH' ,'MBMSPERF' ,'MBMSSCCPCH' ,'MBMSSWITCH' ,'MBTSGUID' ,'MCCHPERIODCOEF' ,'MCDRD' ,'MCLDR' ,'MDTLCS' ,'MGWTST' ,'MNTMODE' ,'MPT' ,'MRCTRL' ,'MRSCOPECTRL' ,'MSCH' ,'MSCHDYNTFS' ,'MSCHFACH' ,'MSCHPARA' ,'MSGSOFTPARA' ,'MTCH' ,'MTCHDYNTFS' ,'NBMINNERPARA' ,'NBMPARA' ,'NCELLDETECTSWITCH' ,'NEMNT' ,'NODEBAAL2PATH' ,'NODEBAAL2SIGNALLINGPOINT' ,'NODEBBBRES' ,'NODEBBOARD' ,'NODEBCABINET' ,'NODEBCHRLEVEL' ,'NODEBCLSPATIMER' ,'NODEBCPPORT' ,'NODEBEQUIPMENT' ,'NODEBFRAME' ,'NODEBIMAGROUP' ,'NODEBIMALINK' ,'NODEBLICENSEALMTHD' ,'NODEBLOCALCELL' ,'NODEBNAME' ,'NODEBNPSU' ,'NODEBPOWEROUTAGE' ,'NODEBRRU' ,'NODEBRRUCHAIN' ,'NODEBRSVDPARA' ,'NODEBRULEACTIONPARA' ,'NODEBSEC' ,'NODEBSITE' ,'NODEBTRFOVERLOADTHD' ,'NODEBUNILINK' ,'NODEBVER' ,'NODEBVLANCLASS' ,'NODESYNCMONTHD' ,'NRISGSNMAP' ,'NRNCCELL' ,'OBJALMSHLD' ,'OBJAUTHSW' ,'OLPC' ,'OMUCOMMSVCSW' ,'OMUETH' ,'OMUIPRT' ,'OMUPARA' ,'OMUPORT' ,'OP' ,'OPERATORCFGPARA' ,'OPERUSERGBR' ,'OPLOCK' ,'OPSW' ,'OSPWDPOLICY' ,'PACKETFILTERALMPARA' ,'PCCPCH' ,'PCHDYNTFS' ,'PDCPHEADCOMP' ,'PERIODICRTTLCS' ,'PEU' ,'PHYPORT' ,'PMU' ,'POOLPRIMHOSTPOLICY' ,'PORTOSCCTRLPARA' ,'PORTPOLICY' ,'PRACHSLOTFORMAT' ,'PRI2QUE' ,'PSPREFABISCONGCTRL' ,'PSUIS' ,'PSUSRRESBIND' ,'PTTPARAM' ,'PTTSTATETRANS' ,'PWDPOLICY' ,'PWRALMSW' ,'PWRPARA' ,'R99ALGPARA' ,'R99FLOWCTRLSWTCH' ,'RAC' ,'RACHDYNTFS' ,'RACHMEASUREPARA' ,'RDTLOGSWITCH' ,'REDIRECTION' ,'REFTIMEDIFF' ,'RESALLOCRULE' ,'RETPORT' ,'RFDESPARAM' ,'RMPWORKMODE' ,'RNCCBCPUID' ,'RNCMBMSPARA' ,'RNCPOOLCFGCTRL' ,'RNCPOOLSYNCFLAG' ,'RRCESTCAUSE' ,'RRCTRLSWITCH' ,'RRINNERTIMER' ,'RRMCDLCFG' ,'RRRSVDPARA' ,'RRUCHAINBRKPOS' ,'RSCADJTIME' ,'RSVRES' ,'RTWPINITADJ' ,'RULELIBVER' ,'RXATTEN' ,'RXBRANCH' ,'RXSW' ,'SAC' ,'SAS' ,'SATLDM' ,'SAUCENTER' ,'SCCPCHTFC' ,'SCHEDULEPRIOMAP' ,'SCTPTEMPLATE' ,'SCUPORT' ,'SDPA' ,'SDSECPOLICY' ,'SELFCUREPARA' ,'SFP' ,'SGSNNODE' ,'SHARETHD' ,'SINGLEIPSWITCH' ,'SIRDISTOLPC' ,'SLFSLVSW' ,'SMLC' ,'SMTHPWRPARA' ,'SMTHPWRSWTCH' ,'SNTPCLTPARA' ,'SNTPSRVINFO' ,'SPG' ,'SPIWEIGHT' ,'SQICOUNT' ,'SS7PATCHSWITCH' ,'SSLAUTHMODE' ,'SSLCONF' ,'SSLCS' ,'STATETIMER' ,'SUBNET' ,'SUBRACK' ,'SUBSYS' ,'SYNCETH' ,'SYNSWITCH' ,'TBDSPINFO' ,'TBLANGNO' ,'TCPOOLBSCID' ,'TCRSVPARA' ,'TCU' ,'TGPSCP' ,'THPCLASS' ,'TIMETHRD' ,'TLFRSWITCH' ,'TLSPOLICY' ,'TNALMPARA' ,'TNLOADBALANCEPARA' ,'TNRSVDPARA' ,'TRAFFICOVERLOADTHD' ,'TRANSCFGSPEC' ,'TRANSPATCHPARA' ,'TRANSPHYLNKPARA' ,'TRANSRSVPARA' ,'TRCLOGSPD' ,'TRPCHKPOLICY' ,'TXBRANCH' ,'TXSW' ,'TYPRABBASIC' ,'TYPRABDCCCMC' ,'TYPRABDYNTF' ,'TYPRABHSPA' ,'TYPRABHSUPAPC' ,'TYPRABOLPC' ,'TYPRABQUALITYMEAS' ,'TYPRABRLC' ,'TYPRABSEMISTATICTF' ,'TYPRABSUBFLOW' ,'TYPRABTOAW' ,'TYPSRBBASIC' ,'TYPSRBDYNTF' ,'TYPSRBHSPA' ,'TYPSRBHSUPAPC' ,'TYPSRBOLPC' ,'TYPSRBRLC' ,'TYPSRBSEMISTATICTF' ,'TYPSRBTOAW' ,'U2LTEHONCOV' ,'UALGORSVPARA' ,'UALGORSVPARAPHY' ,'UALMTHD' ,'UAMRBLACKBOXCTRL' ,'UAPPSERVMEA' ,'UARPTOPRIOMAP' ,'UBLACKBOXSWITCH' ,'UCAMPSTRATFORMASS' ,'UCAPARATERANGE' ,'UCBSIUBCITFTIMER' ,'UCDRFILE' ,'UCELLALGORSVPARA' ,'UCELLAUTOHOMING' ,'UCELLAUTONCELLDETECT' ,'UCELLCMUSERNUM' ,'UCELLIDLEMODETIMER' ,'UCERRMTIMER' ,'UCHRCTRL' ,'UCHRSCOPE' ,'UCHRSTORE' ,'UCNNODERSVPARA' ,'UCPUPFLEXCFG' ,'UCTRLPLNFCPARA' ,'UDCHENHPARA' ,'UDCHTHDRATERATIO' ,'UDEURSVPARA' ,'UDPB' ,'UDPPING' ,'UDSSPARA' ,'UE2EQOSPARA' ,'UEDCHTHDRATERATIO' ,'UEIU' ,'UEKPIPARA' ,'UERACHBASIC' ,'UESTATETRANS' ,'UESTATETRANSTIMER' ,'UEVENTCHRCTRL' ,'UEVENTCHRFCCPUTHD' ,'UEVENTCHRSWITCH' ,'UFACHCFGPARA' ,'UGTPU' ,'UHOSTRNC' ,'UIOPTATOMRULE' ,'UIOPTFEATURE' ,'UIOPTFUNCTION' ,'UIOPTRULE' ,'UIOPTRULELINKRELAT' ,'UIOPTRULEMEMBER' ,'UIUBTRIGHOPARA' ,'UKPISELFCUREPARA' ,'UL2RSVPARA' ,'ULGROUP' ,'ULOCELLNOACCESSPARA' ,'ULOCELLR99ALGPARA' ,'ULOCELLRSVDPARA' ,'ULOCHPRIO' ,'UMMCHRRPTTYPE' ,'UMMCHRSCOPE' ,'UMMEVENTCHRCTRL' ,'UMMMRCTRL' ,'UMMMRSCOPE' ,'UMMRNCCHRSCOPE' ,'UMMRNCMRSCOPE' ,'UMONDEVGRPID' ,'UMRCTRL' ,'UMRSCOPE' ,'UMTESTPARA' ,'UNBMPARA' ,'UNETAWARENESS' ,'UNIUCFGDATA' ,'UNIURSVPARA' ,'UNODEPARA' ,'UNRNCRSVPARA' ,'UPCHRCFG' ,'UPERIODICRTTLCS' ,'UPOOLFLOWCTRLPARA' ,'UPOOLRELIABILITYPARA' ,'URLPWROFFSET' ,'URNCCBCPUID' ,'URNCCHRSCOPE' ,'URNCMRSCOPE' ,'URNCPOOLCFGCTRL' ,'URNCPOOLSYNCFLAG' ,'URRLOGPRINTSWITCH' ,'USAUFUNCTION' ,'USB' ,'USCENARIO' ,'USCENARIOIDENTIFY' ,'USCENARIORULE' ,'USCENARIORULEMEMBER' ,'USCENECFG' ,'USCHEDULEPRIOMAPEX' ,'USCU' ,'USEREVTRTNPOLICY' ,'USEREXPESTIMATE' ,'USEREXPTHD' ,'USERHAPPYBR' ,'USERPLNSHAREPARA' ,'USERVFCPRIO' ,'USERVMEARANGE' ,'USQICOUNT' ,'USRRESBIND' ,'UTGPSCP' ,'UTYPRABDYNTF' ,'UTYPRABHSUPAPC' ,'UTYPRABSUBFLOW' ,'UTYPRABTOAW' ,'UTYPSRBBASIC' ,'UTYPSRBDCHRNCRLC' ,'UTYPSRBDYNTF' ,'UTYPSRBHSPA' ,'UTYPSRBHSUPAPC' ,'UTYPSRBOLPC' ,'UTYPSRBRLC' ,'UTYPSRBSEMISTATICTF' ,'UTYPSRBTOAW' ,'UUPRSVPARA' ,'UUPTSSWITCH' ,'UUSERGBREX' ,'UUSERINTEGPRIO' ,'UUUBOOST' ,'UVIPTRACESW' ,'UX2CTRLPARA' ,'VIPTRACESW' ,'VSWRALMPARAM' ,'VSWRLIMIT' ,'WEBLMT' ,'WEBLOGINPOLICY' ,'WPSALGO' ,'XPUPORT' ]
        blacklist = ['2GHASHKEY', '2GUSERIDANONSWITCH', '3GHASHKEY', '3GUSERIDANONSWITCH', 'ABISE1T1', 'ACALGO',
                     'ACDCVLIMIT', 'ADMCTRL', 'ALDPWRSW', 'AMRC', 'AMRCWB', 'BAMIPRT', 'BATATPA', 'BCFCVOLTAGE',
                     'BEDLPWRDIFF', 'BERTHRESHOLD', 'BRDADMINSTATE', 'BRDHSUPA', 'BRDSTALMSHLD', 'BSC6900EQUIPMENT',
                     'BSC6900GSMFUNCTION', 'BSC6900UMTSFUNCTION', 'BSC6910EQUIPMENT', 'BSC6910GSMFUNCTION',
                     'BSC6910UMTSFUNCTION', 'BSCINNSOFT', 'BSCINNTMR', 'BSCPSINNERSOFTPARA', 'BSCSTATATTR', 'BSCUDBO',
                     'BTSBRDCAP', 'BTSPWRSHARE', 'BTSPWRTYPE', 'BTSRSTINFOEFFECT', 'BTSRSTLIST', 'CALLSHOCKCTRL',
                     'CAPARATERANGE', 'CBSADDR', 'CBSIUBCITFTIMER', 'CDRFILE', 'CELLAUTOHOMING', 'CELLCBSDRX',
                     'CELLDSACMANUALPARA', 'CELLEFACH', 'CELLFRC', 'CELLHSDPCCH', 'CELLLDB', 'CELLLICENSE',
                     'CELLMBDRINTERRAT', 'CELLNFREQPRIOINFO', 'CELLPUC', 'CELLQUALITYMEAS', 'CELLREDIRECTION',
                     'CELLRLACTTIME', 'CELLU2LTEHONCOV', 'CERRMTIMER', 'CHGTHRSHOLD', 'CHK', 'CHRLEVEL', 'CHRRNCCTRL',
                     'CHRSCOPECTRL', 'CHRSW', 'CIDCHG', 'CLSPATIMER', 'CNTCHK', 'CONFIGURE', 'CORRMPARA', 'CPU',
                     'CSPRECTRL', 'CTCH', 'CTFTST', 'CTRLPLNFCPARA', 'CTRLPLNSHAREPARA', 'DCHTHDRATERATIO',
                     'DELAYCLASS', 'DELAYUPDATE', 'DESENS', 'DEVSOFTPARA', 'DISTANCEREDIRECTION', 'DLGROUP', 'DPB',
                     'DRD', 'DRDMIMO', 'DSACAUTOALGO', 'DSSPARA', 'DTXDRXPARA', 'E1T1WM', 'E1T1WORKMODE', 'E2EQOSPARA',
                     'EDCHTHDRATERATIO', 'EDCHTTIRECFG', 'EMSTZ', 'ERACHBASIC', 'EVENTCHRCTRL', 'FACHBANDWIDTH',
                     'FACHDYNTFS', 'FACHLOCH', 'FACHSCHEPRIO', 'FANALMSW', 'FDPCHPARA', 'FDPCHRLPWR',
                     'FLTCORRENABLECFG', 'FPMUX', 'FRAMEMODE', 'FRMHANDPRIO', 'GCELLBTSSOFT', 'GCELLINNHOBASI',
                     'GCELLINNSOFT', 'GCELLINNTMR', 'GCELLSTATOPTPARA', 'GMMCSCHRCTRL', 'GMMCSCHRSCOPE', 'GMMMRCTRL',
                     'GMMMRSCOPE', 'GMMPSCHRCTRL', 'GMMPSCHRSCOPE', 'GPSDELAY', 'GSMCELL', 'GSMNCELL', 'HCSHO',
                     'HSDPAFLOWCTRLPARA', 'HSDPCCH', 'HSSCCHLESSOPPARA', 'HTPROTECT', 'HWVER', 'IFOFFSET', 'IMBDYNTFS',
                     'IMBFACH', 'IMBSEMISTATICTF', 'IMBSWITCH', 'IMEITAC', 'INNSOFTPARA', 'INTERFREQHONCOV',
                     'INTERRATHONCOV', 'INVENTORYANTENNA', 'INVENTORYBOARD', 'INVENTORYBTSANTENNA', 'INVENTORYBTSBOARD',
                     'INVENTORYBTSFRAME', 'INVENTORYBTSHOSTVER', 'INVENTORYBTSRACK', 'INVENTORYBTSSLOT',
                     'INVENTORYFRAME', 'INVENTORYHOSTVER', 'INVENTORYPORT', 'INVENTORYRACK', 'INVENTORYSLOT',
                     'ITELSHUTDOWN', 'IUBTRIGHOPARA', 'IUTIMERANDNUM', 'KPIALMTHD', 'KPISELFCUREPARA', 'LAPDLINK',
                     'LCPSW', 'LDM', 'LNKSRC', 'LOADTLIMIT', 'LOCELLPRI', 'LOCHPRIO', 'LTECELL', 'LTENCELL',
                     'MAXDSPFLTNUM', 'MBMSALARMPARA', 'MBMSFACH', 'MBMSPERF', 'MBMSSCCPCH', 'MBMSSWITCH', 'MBTSGUID',
                     'MCCHPERIODCOEF', 'MCDRD', 'MCLDR', 'MGWTST', 'MRCTRL', 'MRSCOPECTRL', 'MSCH', 'MSCHDYNTFS',
                     'MSCHFACH', 'MSCHPARA', 'MTCH', 'MTCHDYNTFS', 'NBMINNERPARA', 'NBMPARA', 'NCELLDETECTSWITCH',
                     'NODEBAAL2PATH', 'NODEBAAL2SIGNALLINGPOINT', 'NODEBBOARD', 'NODEBCABINET', 'NODEBCPPORT',
                     'NODEBEQUIPMENT', 'NODEBFRAME', 'NODEBIMAGROUP', 'NODEBIMALINK', 'NODEBLOCALCELL', 'NODEBNAME',
                     'NODEBNPSU', 'NODEBRRU', 'NODEBRRUCHAIN', 'NODEBSEC', 'NODEBSITE', 'NODEBUNILINK', 'NODEBVER',
                     'NODEBVLANCLASS', 'NODESYNCMONTHD', 'NRNCCELL', 'OLPC', 'OPERATORCFGPARA', 'OPERUSERGBR', 'PCCPCH',
                     'PCHDYNTFS', 'PDCPHEADCOMP', 'PERIODICRTTLCS', 'POOLPRIMHOSTPOLICY', 'PRACHSLOTFORMAT', 'PTTPARAM',
                     'PTTSTATETRANS', 'R99ALGPARA', 'R99FLOWCTRLSWTCH', 'RAC', 'RACHDYNTFS', 'RACHMEASUREPARA',
                     'RDTLOGSWITCH', 'REDIRECTION', 'REFTIMEDIFF', 'RESALLOCRULE', 'RFDESPARAM', 'RMPWORKMODE',
                     'RNCCBCPUID', 'RNCMBMSPARA', 'RNCPOOLCFGCTRL', 'RNCPOOLSYNCFLAG', 'RRCESTCAUSE', 'RRCTRLSWITCH',
                     'RRINNERTIMER', 'RRMCDLCFG', 'RRRSVDPARA', 'RRUCHAINBRKPOS', 'RTWPINITADJ', 'RXATTEN', 'RXSW',
                     'SAC', 'SAS', 'SATLDM', 'SCCPCHTFC', 'SCHEDULEPRIOMAP', 'SDPA', 'SDSECPOLICY', 'SELFCUREPARA',
                     'SIRDISTOLPC', 'SMLC', 'SMTHPWRPARA', 'SMTHPWRSWTCH', 'SPG', 'SPIWEIGHT', 'SQICOUNT', 'STATETIMER',
                     'TBDSPINFO', 'TBLANGNO', 'TCPOOLBSCID', 'TGPSCP', 'THPCLASS', 'TLFRSWITCH', 'TRAFFICOVERLOADTHD',
                     'TXSW', 'TYPRABBASIC', 'TYPRABDCCCMC', 'TYPRABDYNTF', 'TYPRABHSPA', 'TYPRABHSUPAPC', 'TYPRABOLPC',
                     'TYPRABQUALITYMEAS', 'TYPRABRLC', 'TYPRABSEMISTATICTF', 'TYPRABSUBFLOW', 'TYPRABTOAW',
                     'TYPSRBBASIC', 'TYPSRBDYNTF', 'TYPSRBHSPA', 'TYPSRBHSUPAPC', 'TYPSRBOLPC', 'TYPSRBRLC',
                     'TYPSRBSEMISTATICTF', 'TYPSRBTOAW', 'U2LTEHONCOV', 'UEKPIPARA', 'UESTATETRANS',
                     'UESTATETRANSTIMER', 'ULGROUP', 'UMMCHRRPTTYPE', 'UMMCHRSCOPE', 'UMMEVENTCHRCTRL', 'UMMMRCTRL',
                     'UMMMRSCOPE', 'UMMRNCCHRSCOPE', 'UMMRNCMRSCOPE', 'USCENARIOIDENTIFY', 'USERHAPPYBR',
                     'USERPLNSHAREPARA', 'UUPTSSWITCH', 'UUUBOOST', 'VIPTRACESW', 'VSWRALMPARAM', 'VSWRLIMIT',
                     'WPSALGO']
        headerInfo = dict()

        headerInfo['DATETIME'] = (datetime.strptime(match.group('dateTime'), "%Y%m%d%H")).strftime('%Y-%m-%d %H:00:00')
        headerInfo['ELEMENTNAME'] = match.group('elementName')
        headerInfo['OBJECT'] = headerInfo['ELEMENTNAME']
        headerInfo['NE_NAME'] = headerInfo['ELEMENTNAME']
        headerInfo["BSC_NAME"] = headerInfo["ELEMENTNAME"]
        headerInfo["RNC_NAME"] = headerInfo["ELEMENTNAME"]
        headerInfo['GRANULARITY PERIOD'] = 1440
        try:
            timestamp = familyObj.parseEnvelopeDataTime(headerInfo['DATETIME'])
        except ValueError as e:
            logger.warning("Could not build mediationEnvelope due to {0}: ".format(e), __file__)

        file_class_name = ''
        parse = False
        newDocument = dict()
        for event, elem in context:
            if event == 'start':
                if elem.tag == 'class':
                    name = elem.get('name').decode("latin-1")
                    if file_class_name == '':
                        file_class_name = name.upper()
                        prefix_class_name = name.upper()
                        continue
                    # ignorar primeiro class (nivel acima)

                    parse = True
                    if '_' in name:
                        class_name, prefix_class = self.processClass(name.upper())
                    else:
                        class_name = name.upper()
                        prefix_class = prefix_class_name.upper()

                    try:
                        class_name = modelsMapping[file_class_name][class_name]
                    except Exception as e:
                        # logger.warning("Could not map class_name \"{0}\": {1}".format(class_name, e))
                        pass
                    try:
                        # Verify if family is to parse
                        if class_name in blacklist:
                            parse = False
                        elif not hm.validateClass(class_name):
                            # logger.warning("Could not FDN map class_name \"{0}\": {1}".format(class_name, e))
                            parse = False
                    except Exception as e:
                        # logger.warning("Something went wrong with class_name \"{0}\": {1}".format(class_name, e))
                        parse = False

                elif elem.tag == 'object' and parse:
                    newDocument = copy.deepcopy(headerInfo)
                    newDocument["NECLASSNAME"] = file_class_name
                    newDocument["CLASSNAME"] = class_name
                    newDocument["P"] = prefix_class
                    elem.clear()

                elif elem.tag == 'parameter' and parse:
                    try:
                        param_name = elem.get('name').decode("latin-1").upper()
                        param_value = elem.get('value').decode("latin-1")
                        if newDocument.has_key(param_name):
                            logger.warning("Duplicated parameter name '{0}'".format(param_name))
                            continue
                        else:
                            newDocument[param_name] = param_value
                    except Exception as e:
                        try:
                            param_name = elem.get('name').decode("latin-1").upper()
                            param_value = elem.get('value').encode('utf-8', 'ignore').decode('utf-8')
                            newDocument[param_name] = param_value
                        except:
                            logger.warning('Value not accepted: {0}'.format(e))

            elif event == 'end':
                if elem.tag == 'object' and parse and newDocument != dict():
                    newDocument = hm.buildFDN(newDocument)
                    # ALGUNS IDS QUE CORRESPONDEM AO CELLID OU LOCALCELLID
                    if "CELLID" not in newDocument:
                        if "GLOCELLID" in newDocument:
                            newDocument["CELLID"] = newDocument["GLOCELLID"]
                        elif 'SRC2GNCELLID' in newDocument:
                            newDocument["CELLID"] = newDocument['SRC2GNCELLID']
                        elif 'SRC3GNCELLID' in newDocument:
                            newDocument["CELLID"] = newDocument["SRC3GNCELLID"]
                        elif 'SRCLTENCELLID' in newDocument:
                            newDocument["CELLID"] = newDocument["SRCLTENCELLID"]
                        elif 'INNCELLID' in newDocument:
                            newDocument["CELLID"] = newDocument["INNCELLID"]

                    if 'PRIMARYLOCALCELLID' in newDocument:
                        newDocument["LOCALCELLID"] = newDocument["PRIMARYLOCALCELLID"]

                    newDocument = self.enrichProcess(baseObject, headerInfo['ELEMENTNAME'], newDocument)
                    if newDocument['CLASSNAME'] == 'UCELL':
                        mongoDocument = self.enrichDocument(newDocument)
                        self._mongoConnection.executeQuery(
                            {"query": {"CORRKEY": mongoDocument['CORRKEY']}, "set": mongoDocument}, 'upSert')

                    familyObj.clearDocuments()
                    familyObj.setUnitID(newDocument["CLASSNAME"])
                    familyObj.addDocument({"dataTime": timestamp, "granularitySec": 1440, "data": newDocument})
                    self.nextOp(familyObj=familyObj, baseObject=baseObject)
                    elem.clear()
                    newDocument = dict()
            else:
                elem.clear()
        del context

    def enrichData(self, filePath, controller_name, baseObject):
        try:
            context = iter(etree.iterparse(filePath, events=('start', 'end'), tag=('class', 'object', 'parameter')))
        except etree.ParseError:
            logger.warning("Malformed HUAWEI Parameter GExport XML file '{0}'".format(filePath))
            return enrichmentData

        unitsToGet = ['NBIOTCELL', 'CELL', 'NODEB', 'ENODEBFUNCTION', 'UCELL', 'GCELL', 'BTS', 'NRCELL',
                      'GNODEBFUNCTION']
        fieldsList = ['ENODEBFUNCTIONNAME', 'CELLNAME', 'CELLID', 'LOCALCELLID', 'ENODEBID', 'LOGICRNCID', 'NODEBID',
                      'NODEBNAME', 'CELLID', 'CELLNAME', 'CI', 'BTSID', 'BTSNAME', 'GNODEBFUNCTIONNAME', 'NRCELLID',
                      'GNBID']

        file_class_name = ''
        newDocument = dict()
        toProcess = False
        class_name = ''
        for event, elem in context:
            if event == 'start':
                if elem.tag == 'class':
                    name = elem.get('name').decode("latin-1")
                    if file_class_name == '':
                        file_class_name = name.upper()
                        continue

                    if '_' in name:
                        class_name, prefix_class = self.processClass(name.upper())
                    else:
                        class_name = name.upper()
                        prefix_class = file_class_name.upper()

                    if class_name in unitsToGet:
                        toProcess = True

                elif elem.tag == 'parameter' and toProcess:
                    elName = elem.get('name').decode("latin-1").upper()
                    if toProcess and elName in fieldsList:
                        try:
                            newDocument[elName] = elem.get('value').decode("latin-1")
                        except:
                            newDocument[elName] = elem.get('value')

            elif event == 'end':
                if elem.tag == 'object':
                    # 2G
                    if file_class_name in ['BSC6900GSM', 'BSC6910GSM']:
                        if class_name == 'GCELL':
                            if "CI" in newDocument and "CELLNAME" in newDocument and "BTSID" in newDocument and "CELLID" in newDocument:

                                if newDocument["CELLID"] not in baseObject.enrich_cell_dict:
                                    baseObject.enrich_cell_dict[newDocument["CELLID"]] = dict()

                                cell_obj = CellObject(newDocument["CELLID"], newDocument["CELLNAME"], newDocument["CI"],
                                                      newDocument["BTSID"], None, controller_name, "2G")
                                baseObject.enrich_cell_dict[newDocument["CELLID"]][controller_name] = cell_obj

                                cellname_key = newDocument["CELLNAME"] + "_2G"
                                if cellname_key not in baseObject.enrich_cell_dict:
                                    baseObject.enrich_cell_dict[cellname_key] = dict()

                                baseObject.enrich_cell_dict[cellname_key] = (newDocument["CELLID"], controller_name)

                        elif class_name == 'BTS':

                            if "BTSID" in newDocument and "BTSNAME" in newDocument:

                                # BTSID --> BTSNAME
                                bts_id_key = newDocument["BTSID"] + "_2G"
                                if bts_id_key not in baseObject.enrich_site_dict:
                                    baseObject.enrich_site_dict[bts_id_key] = dict()

                                site_obj = SiteObject(newDocument["BTSID"], newDocument["BTSNAME"], controller_name,
                                                      "2G")
                                baseObject.enrich_site_dict[bts_id_key][controller_name] = site_obj

                                # BTSNAME --> BTSID
                                bts_name_key = newDocument["BTSNAME"] + "_2G"
                                if bts_name_key not in baseObject.enrich_site_dict:
                                    baseObject.enrich_site_dict[bts_name_key] = dict()

                                baseObject.enrich_site_dict[bts_name_key] = (newDocument["BTSID"], controller_name)

                    # 3G
                    elif file_class_name == 'BSC6910UMTS':

                        if class_name == "UCELL":

                            if 'LOGICRNCID' in newDocument and 'NODEBID' in newDocument and 'NODEBNAME' in newDocument and 'CELLID' in newDocument \
                                    and 'CELLNAME' in newDocument:

                                if newDocument["CELLID"] not in baseObject.enrich_cell_dict:
                                    baseObject.enrich_cell_dict[newDocument["CELLID"]] = dict()

                                cell_obj = CellObject(newDocument["CELLID"], newDocument["CELLNAME"], None,
                                                      newDocument["NODEBID"], newDocument["NODEBNAME"], controller_name,
                                                      "3G")
                                baseObject.enrich_cell_dict[newDocument["CELLID"]][controller_name] = cell_obj

                                cellname_key = newDocument["CELLNAME"] + "_3G"
                                if cellname_key not in baseObject.enrich_cell_dict:
                                    baseObject.enrich_cell_dict[cellname_key] = dict()

                                baseObject.enrich_cell_dict[cellname_key] = (newDocument["CELLID"], controller_name)

                                # NODEBID --> NODEBNAME
                                nodeb_id_key = newDocument["NODEBID"] + "_3G"
                                if nodeb_id_key not in baseObject.enrich_site_dict:
                                    baseObject.enrich_site_dict[nodeb_id_key] = dict()

                                site_obj = SiteObject(newDocument["NODEBID"], newDocument["NODEBNAME"], controller_name,
                                                      "3G")
                                baseObject.enrich_site_dict[nodeb_id_key][controller_name] = site_obj

                                # NODEBNAME --> NODEBID
                                nodeb_name_key = newDocument["NODEBNAME"] + "_3G"
                                if nodeb_name_key not in baseObject.enrich_site_dict:
                                    baseObject.enrich_site_dict[nodeb_name_key] = dict()

                                baseObject.enrich_site_dict[nodeb_name_key] = (newDocument["NODEBID"], controller_name)

                                # so consigo em 3G, porque tras o LOGICRNCID
                                if newDocument["LOGICRNCID"] not in baseObject.enrich_controller_dict:
                                    baseObject.enrich_controller_dict[newDocument["LOGICRNCID"]] = dict()

                                baseObject.enrich_controller_dict[newDocument["LOGICRNCID"]] = controller_name

                        elif class_name == "NODEB":
                            if 'LOGICRNCID' in newDocument and 'NODEBID' in newDocument and 'NODEBNAME' in newDocument:
                                # NODEBID --> NODEBNAME
                                nodeb_id_key = newDocument["NODEBID"] + "_3G"
                                if nodeb_id_key not in baseObject.enrich_site_dict:
                                    baseObject.enrich_site_dict[nodeb_id_key] = dict()

                                site_obj = SiteObject(newDocument["NODEBID"], newDocument["NODEBNAME"], controller_name,
                                                      "3G")
                                baseObject.enrich_site_dict[nodeb_id_key][controller_name] = site_obj

                                # NODEBNAME --> NODEBID
                                nodeb_name_key = newDocument["NODEBNAME"] + "_3G"
                                if nodeb_name_key not in baseObject.enrich_site_dict:
                                    baseObject.enrich_site_dict[nodeb_name_key] = dict()

                                baseObject.enrich_site_dict[nodeb_name_key] = (newDocument["NODEBID"], controller_name)

                                # so consigo em 3G, porque tras o LOGICRNCID
                                if newDocument["LOGICRNCID"] not in baseObject.enrich_controller_dict:
                                    baseObject.enrich_controller_dict[newDocument["LOGICRNCID"]] = dict()

                                baseObject.enrich_controller_dict[newDocument["LOGICRNCID"]] = controller_name

                    # 4G/5G
                    else:
                        # 4G
                        if class_name in ['CELL', 'NBIOTCELL']:

                            if "ENODEBFUNCTIONNAME" in newDocument and "CELLNAME" in newDocument:

                                # as samples podem trazer CELLID, LOCALCELLID ou ambos
                                if "CELLID" in newDocument:
                                    key = newDocument["CELLID"] + "_" + newDocument["ENODEBFUNCTIONNAME"]

                                    cell_obj = CellObject(newDocument["CELLID"], newDocument["CELLNAME"], None, None,
                                                          newDocument["ENODEBFUNCTIONNAME"], None, "4G")
                                    baseObject.enrich_cell_dict[key] = cell_obj

                                if "LOCALCELLID" in newDocument:
                                    key = newDocument["LOCALCELLID"] + "_" + newDocument["ENODEBFUNCTIONNAME"]

                                    cell_obj = CellObject(newDocument["CELLID"], newDocument["CELLNAME"],
                                                          newDocument["LOCALCELLID"], None,
                                                          newDocument["ENODEBFUNCTIONNAME"], None, "4G")
                                    baseObject.enrich_localcell_dict[key] = cell_obj

                        elif class_name == 'ENODEBFUNCTION':

                            if "ENODEBFUNCTIONNAME" in newDocument and "ENODEBID" in newDocument:

                                site_obj = SiteObject(newDocument["ENODEBID"], newDocument["ENODEBFUNCTIONNAME"], None,
                                                      "4G")
                                baseObject.enrich_site_dict[newDocument["ENODEBFUNCTIONNAME"]] = site_obj

                                enodeb_key = newDocument["ENODEBID"] + "_4G"
                                if enodeb_key not in baseObject.enrich_site_dict:
                                    baseObject.enrich_site_dict[enodeb_key] = dict()

                                baseObject.enrich_site_dict[enodeb_key] = newDocument["ENODEBFUNCTIONNAME"]

                        # 5G
                        if class_name == "NRCELL":
                            if "GNODEBFUNCTIONNAME" in newDocument and "CELLNAME" in newDocument:

                                # as samples podem trazer NRCELLID, CELLID ou ambos
                                if "NRCELLID" in newDocument:
                                    key = newDocument["NRCELLID"] + "_" + newDocument["GNODEBFUNCTIONNAME"]

                                    cell_obj = CellObject(newDocument["NRCELLID"], newDocument["CELLNAME"], None, None,
                                                          newDocument["GNODEBFUNCTIONNAME"], None, "5G")
                                    baseObject.enrich_cell_dict[key] = cell_obj

                                if "CELLID" in newDocument:
                                    key = newDocument["CELLID"] + "_" + newDocument["GNODEBFUNCTIONNAME"]

                                    cell_obj = CellObject(newDocument["NRCELLID"], newDocument["CELLNAME"],
                                                          newDocument["CELLID"], None,
                                                          newDocument["GNODEBFUNCTIONNAME"], None, "5G")
                                    baseObject.enrich_localcell_dict[key] = cell_obj

                        elif class_name == 'GNODEBFUNCTION':

                            if "GNODEBFUNCTIONNAME" in newDocument and "GNBID" in newDocument:

                                site_obj = SiteObject(newDocument["GNBID"], newDocument["GNODEBFUNCTIONNAME"], None,
                                                      "5G")
                                baseObject.enrich_site_dict[newDocument["GNODEBFUNCTIONNAME"]] = site_obj

                                enodeb_key = newDocument["GNBID"] + "_5G"
                                if enodeb_key not in baseObject.enrich_site_dict:
                                    baseObject.enrich_site_dict[enodeb_key] = dict()

                                baseObject.enrich_site_dict[enodeb_key] = newDocument["GNODEBFUNCTIONNAME"]

                    parametersData = dict()
                    newDocument = dict()
                elif elem.tag == 'class':
                    toProcess = False
                    class_name = ''

                elem.clear()
        del context
        return baseObject

    def processClass(self, name):
        name = name.rsplit("_", 1)
        class_name = name[0]
        prefix_class = name[1]
        return class_name, prefix_class

    def enrichProcess(self, baseObject, controller_name, newDocument):
        ### PARA FICHEIROS SRAN ###
        if newDocument["NECLASSNAME"] == "BTS3900" or newDocument["NECLASSNAME"] == "BTS5900":
            # 5G
            if "GNODEBFUNCTIONNAME" in newDocument:
                if newDocument["GNODEBFUNCTIONNAME"] in baseObject.enrich_site_dict:
                    # ENRIQUECER O SITE
                    newDocument.update(baseObject.enrich_site_dict[newDocument["GNODEBFUNCTIONNAME"]].get_site_name())
                    if "NRDUCELLID" in newDocument:
                        newDocument["NRCELLID"] = newDocument["NRDUCELLID"]

                    # Preencher NEIG_CELL_ID
                    if newDocument["CLASSNAME"].upper() == "EUTRANINTRAFREQNCELL" or newDocument[
                        "CLASSNAME"].upper() == "EUTRANINTERFREQNCELL":
                        if "NRCELLID" in newDocument and "GNODEBID" in newDocument:
                            newDocument["NEIGH_CELL_ID"] = str(
                                int(newDocument["GNODEBID"]) * 16384 + int(newDocument["NRCELLID"]))

                    if "NRCELLID" in newDocument:
                        cell_key = newDocument["NRCELLID"] + "_" + newDocument["GNODEBFUNCTIONNAME"]

                        try:
                            newDocument.update(baseObject.enrich_cell_dict[cell_key].get_cell_name())
                        except Exception as e:
                            pass

                        newDocument["CELL_ID"] = str(int(
                            baseObject.enrich_site_dict[newDocument["GNODEBFUNCTIONNAME"]].get_site_id()) * 16384 + int(
                            newDocument["NRCELLID"]))

                    elif "LOCALCELLID" in newDocument:
                        cell_key = newDocument["LOCALCELLID"] + "_" + newDocument["GNODEBFUNCTIONNAME"]

                        try:
                            newDocument.update(baseObject.enrich_localcell_dict[cell_key].get_cell_name())
                            newDocument["CELL_ID"] = str(int(baseObject.enrich_site_dict[newDocument[
                                "GNODEBFUNCTIONNAME"]].get_site_id()) * 16384 + int(
                                baseObject.enrich_localcell_dict[cell_key].get_ci_or_localcellid()))
                        except Exception as e:
                            pass

                if "GNODEB_NAME" not in newDocument:
                    newDocument["GNODEB_NAME"] = newDocument["GNODEBFUNCTIONNAME"]

            # 4G
            if "ENODEBFUNCTIONNAME" in newDocument:
                if newDocument["ENODEBFUNCTIONNAME"] in baseObject.enrich_site_dict:
                    # ENRIQUECER O SITE
                    newDocument.update(baseObject.enrich_site_dict[newDocument["ENODEBFUNCTIONNAME"]].get_site_name())

                    # Preencher NEIG_CELL_ID
                    if newDocument["CLASSNAME"].upper() == "EUTRANINTRAFREQNCELL" or newDocument[
                        "CLASSNAME"].upper() == "EUTRANINTERFREQNCELL":
                        if "CELLID" in newDocument and "ENODEBID" in newDocument:
                            newDocument["NEIGH_CELL_ID"] = str(
                                int(newDocument["ENODEBID"]) * 256 + int(newDocument["CELLID"]))

                    if "CELLID" in newDocument:
                        cell_key = newDocument["CELLID"] + "_" + newDocument["ENODEBFUNCTIONNAME"]

                        try:
                            newDocument.update(baseObject.enrich_cell_dict[cell_key].get_cell_name())
                        except Exception as e:
                            pass

                        newDocument["CELL_ID"] = str(int(
                            baseObject.enrich_site_dict[newDocument["ENODEBFUNCTIONNAME"]].get_site_id()) * 256 + int(
                            newDocument["CELLID"]))

                    if "LOCALCELLID" in newDocument:
                        cell_key = newDocument["LOCALCELLID"] + "_" + newDocument["ENODEBFUNCTIONNAME"]

                        try:
                            newDocument.update(baseObject.enrich_localcell_dict[cell_key].get_cell_name())
                            newDocument["CELL_ID"] = str(int(baseObject.enrich_site_dict[newDocument[
                                "ENODEBFUNCTIONNAME"]].get_site_id()) * 256 + int(
                                baseObject.enrich_localcell_dict[cell_key].get_ci_or_localcellid()))
                        except Exception as e:
                            pass

                if "ENODEB_NAME" not in newDocument:
                    newDocument["ENODEB_NAME"] = newDocument["ENODEBFUNCTIONNAME"]

            # 3G
            if "NODEBFUNCTIONNAME" in newDocument:
                try:
                    nodeb_id = baseObject.enrich_site_dict[newDocument["NODEBFUNCTIONNAME"] + "_3G"][0]
                    rnc_name = baseObject.enrich_site_dict[newDocument["NODEBFUNCTIONNAME"] + "_3G"][1]
                    # CONTROLADOR
                    # newDocument.update(baseObject.enrich_site_dict[nodeb_id + "_3G"].get_controller_name())
                    newDocument["RNC_NAME"] = rnc_name
                    # SITE
                    newDocument.update(baseObject.enrich_site_dict[nodeb_id + "_3G"][rnc_name].get_site_name())
                # CELULA (ver como enriquecer a celula)

                except KeyError:
                    if "NODEB_NAME" not in newDocument:
                        newDocument["NODEB_NAME"] = newDocument["NODEBFUNCTIONNAME"]

            # 2G
            if "GBTSFUNCTIONNAME" in newDocument:
                try:
                    bts_id = baseObject.enrich_site_dict[newDocument["GBTSFUNCTIONNAME"] + "_2G"][0]
                    bsc_name = baseObject.enrich_site_dict[newDocument["GBTSFUNCTIONNAME"] + "_2G"][1]
                    # CONTROLADOR
                    # newDocument.update(baseObject.enrich_site_dict[bts_id + "_2G"].get_controller_name())
                    newDocument["BSC_NAME"] = bsc_name
                    # SITE
                    newDocument.update(baseObject.enrich_site_dict[bts_id + "_2G"][bsc_name].get_site_name())
                # CELULA (ver como enriquecer a celula)

                except KeyError:
                    if "BTS_NAME" not in newDocument:
                        newDocument["BTS_NAME"] = newDocument["GBTSFUNCTIONNAME"]

        ### FIM DOS FICHEIROS SRAN ###
        else:
            ### FICHEIROS 2G e 3G ###
            # ENRIQUECER O SITE E A CELULA
            if "CELLID" in newDocument:
                if newDocument["CELLID"] in baseObject.enrich_cell_dict:
                    cell_id = ""
                    try:
                        # SITE
                        newDocument.update(
                            baseObject.enrich_cell_dict[newDocument["CELLID"]][controller_name].get_cell_name())
                        # CELULA
                        cell_id = baseObject.enrich_cell_dict[newDocument["CELLID"]][
                            controller_name].get_ci_or_localcellid()
                    except Exception as e:
                        pass

                    # 2G (se tiver o campo CI)
                    if cell_id:
                        try:
                            newDocument["CELL_ID"] = cell_id
                            bts_key = baseObject.enrich_cell_dict[newDocument["CELLID"]][
                                          controller_name].get_site_id() + "_2G"

                            # SITE
                            # if bts_key in baseObject.enrich_site_dict:
                            try:
                                newDocument.update(
                                    baseObject.enrich_site_dict[bts_key][controller_name].get_site_name())
                                newDocument.update(
                                    baseObject.enrich_site_dict[bts_key][controller_name].get_controller_name())
                            except Exception as e:
                                pass

                        except Exception as e:
                            pass
                    # 3G
                    else:
                        try:
                            newDocument["CELL_ID"] = newDocument["CELLID"]
                            nodeb_key = baseObject.enrich_cell_dict[newDocument["CELLID"]][
                                            controller_name].get_site_id() + "_3G"

                            # SITE
                            try:
                                newDocument.update(
                                    baseObject.enrich_site_dict[nodeb_key][controller_name].get_site_name())
                                newDocument.update(
                                    baseObject.enrich_site_dict[nodeb_key][controller_name].get_controller_name())
                            except Exception as e:
                                pass

                        except Exception as e:
                            pass

        # EM ULTIMO CASO, TENTAR PREENCHER O QUE NAO CONSEGUIU ATRAVES DO DICIONARIO
        # CELULA
        if "CELL_NAME" not in newDocument:
            if "CELLNAME" in newDocument:
                newDocument["CELL_NAME"] = newDocument["CELLNAME"]
            elif "LOCALCELLNAME" in newDocument:
                newDocument["CELL_NAME"] = newDocument["LOCALCELLNAME"]

        # SITE 3G
        if "NODEB_NAME" not in newDocument:

            if "NODEBNAME" in newDocument:
                try:
                    nodeb_id = baseObject.enrich_site_dict[newDocument["NODEBNAME"] + "_3G"][0]
                    # CONTROLADOR
                    newDocument.update(
                        baseObject.enrich_site_dict[nodeb_id + "_3G"][controller_name].get_controller_name())
                    # SITE
                    newDocument.update(baseObject.enrich_site_dict[nodeb_id + "_3G"][controller_name].get_site_name())
                # CELULA

                except KeyError:
                    newDocument["NODEB_NAME"] = newDocument["NODEBNAME"]

            if "NODEBID" in newDocument:
                nodeb_key = newDocument["NODEBID"] + "_3G"
                try:
                    newDocument.update(baseObject.enrich_site_dict[nodeb_key][controller_name].get_site_name())
                    newDocument.update(baseObject.enrich_site_dict[nodeb_key][controller_name].get_controller_name())
                except Exception as e:
                    pass

        # SITE 2G
        if "BTS_NAME" not in newDocument:

            if "BTSNAME" in newDocument:
                try:
                    bts_id = baseObject.enrich_site_dict[newDocument["BTSNAME"] + "_2G"][0]
                    # CONTROLADOR
                    newDocument.update(
                        baseObject.enrich_site_dict[bts_id + "_2G"][controller_name].get_controller_name())
                    # SITE
                    newDocument.update(baseObject.enrich_site_dict[bts_id + "_2G"][controller_name].get_site_name())
                # CELULA

                except KeyError:
                    newDocument["BTS_NAME"] = newDocument["BTSNAME"]

            if "BTSID" in newDocument:
                bts_key = newDocument["BTSID"] + "_2G"
                try:
                    if "BTS_NAME" not in newDocument:
                        newDocument.update(baseObject.enrich_site_dict[bts_key][controller_name].get_site_name())

                    if "BSC_NAME" not in newDocument:
                        newDocument.update(baseObject.enrich_site_dict[bts_key][controller_name].get_controller_name())
                except Exception as e:
                    pass

        # CONTROLADOR 3G
        if "RNC_NAME" not in newDocument:
            if "NODEB_NAME" in newDocument:
                try:
                    nodeb_id = baseObject.enrich_site_dict[newDocument["NODEB_NAME"] + "_3G"][0]
                    newDocument.update(
                        baseObject.enrich_site_dict[nodeb_id + "_3G"][controller_name].get_controller_name())
                except Exception as e:
                    pass

        if "RNC_NAME" not in newDocument:
            if "LOGICRNCID" in newDocument:
                try:
                    newDocument["RNC_NAME"] = baseObject.enrich_controller_dict[newDocument["LOGICRNCID"]]
                except Exception as e:
                    pass

            elif "RNCID" in newDocument:
                try:
                    newDocument["RNC_NAME"] = baseObject.enrich_controller_dict[newDocument["RNCID"]]
                except Exception as e:
                    pass

        if "RNC_NAME" not in newDocument:
            try:
                newDocument["RNC_NAME"] = newDocument["RNCNAME"]
            except KeyError:
                if newDocument["NECLASSNAME"] == "BSC6910UMTS":
                    newDocument["RNC_NAME"] = self.getNameFromFile(familyObj.fileName)

        # CONTROLADOR 2G
        if "BSC_NAME" not in newDocument:
            try:
                bsc_id = baseObject.enrich_site_dict[newDocument["BTS_NAME"] + "_2G"][controller_name]
                newDocument.update(baseObject.enrich_site_dict[bsc_id + "_2G"][controller_name].get_controller_name())
            except Exception as e:
                pass

        if "BSC_NAME" not in newDocument:
            try:
                newDocument["BSC_NAME"] = newDocument["BSCNAME"]
            except KeyError:
                if newDocument["NECLASSNAME"] == "BSC6900GSM" or newDocument["NECLASSNAME"] == "BSC6910GSM":
                    newDocument["BSC_NAME"] = self.getNameFromFile(familyObj.fileName)

        return newDocument

    def enrichDocument(self, newDocument):
        mongoDocument = dict()

        for key in self._enrichMapping:
            if key in newDocument:
                mongoDocument[key] = newDocument[key]

        mongoDocument['CORRKEY'] = mongoDocument['FDN']
        return mongoDocument
