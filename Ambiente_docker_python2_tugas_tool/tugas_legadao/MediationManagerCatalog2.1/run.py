
from src.MediationCollectorManager import MediationCollectorManager
import argparse
import os


# #
# Start command line code
# #
if __name__ == '__main__':
	parser = argparse.ArgumentParser(description='Mediation Catalog Manager 2.1: Made by Bruno Silva')

	parser.add_argument("-c", default='c', help='collector configuration name')
	parser.add_argument("-v", metavar='v', help='vendor')
	parser.add_argument("-o", metavar='o', default='create', help='operation to execute (create,merge,etc..)')
	parser.add_argument("-d", default='d', help='documentation')
	parser.add_argument("-vu", default='', help='unified vision')
	parser.add_argument("-s", default='s', help='schema')

	parser.add_argument("-bc", default='bc', help='input catalog base')
	parser.add_argument("-nc", default='nc', help='input new catalog')
	parser.add_argument("-sc", default='sc', help='input shelf catalog')
	parser.add_argument("-sd", default='NA', help='input shelf pack dir')
	parser.add_argument("-n", default='n', help='output catalog nomenclature')
	parser.add_argument("-cf", default='cf', help='compressed flag')
	parser.add_argument("-di", default='di', help='datetime field')
	parser.add_argument("-ne", default='ne', help='network element field')
	parser.add_argument("-mc", default='mc', help='merge configuration directory')
	parser.add_argument("-na", default='na', help='sql for NAMF')
	parser.add_argument("-gu", default='gu', help='granularityUnit')
	parser.add_argument("-gf", default='gf', help='granularityField')
	parser.add_argument("-env", default='prd', help='system envirement')
	parser.add_argument("-sl", help='stats lock', required=False, action='store_true')
	parser.add_argument("-pi", default="false", help='create parameter index')
	parser.add_argument("--liq", action='store_true', required=False, help='create liquibase adapted sql scripts')

	args = parser.parse_args()
	data = dict()
	data['collector'] = args.c
	data['vendor'] = args.v
	data['schema'] = args.s
	data['documentation'] = args.d
	data['unifiedVision'] = args.vu
	data['baseCatalog'] = args.bc
	data['newCatalog'] = args.nc
	data['nomenclature'] = args.n
	data['shelfCatalog'] = args.sc
	data['compressedFlag'] = args.cf
	data['dateIndex'] = args.di
	data['granularityUnit'] = args.gu
	data['granularityField'] = args.gf
	data['shelfPath'] = '' if args.sd in ['sd', ''] else args.sd
	data['networkElement'] = '' if args.ne in ['networkElement', '', 'ne'] else args.ne
	data['namf'] = False if args.na.upper() in ['NA', '', 'FALSE'] else True
	data['mergeConfiguration'] = '' if args.mc in ['mc', ''] else args.mc
	data['envirement'] = args.env
	data['statslock'] = True if args.sl and args.s != 's' else False
	data['parameterindex'] = True if args.pi and args.pi.upper() == 'TRUE' else False
	data['liquibase'] = args.liq

	if not os.path.exists('./output'):
		os.mkdir('output')

	MediationCollectorManager().process(args.o.upper(), data)
