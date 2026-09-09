__doc__ = \
    '''
    PreParser for Parameters NSN using sax
'''

__version__ = '0.1'

__authors__ = [
    "Version 1.0: Bruno Silva <bruno-e-silva@alticelabs.com>"
    "Version 1.1: Rafael Gomes <rafael-g-gomes@alticelabs.com>"
    "Version 1.2: Joao Pio <joao-t-pio@alticelabs.com>"
    "Version 1.3: Marco Jeronimo <marco-a-jeronimo@alticelabs.com>"
    "Version 1.4: Gil Martins <gil-l-martins@alticelabs.com>"
]

import sys, os, json
import datetime
import argparse
import xml.etree.cElementTree as etree


class EricssonEnrichParameter():

    def __init__(self, filePath, memory=dict(), in_memory_node_b=dict(), vendor=None):
        self._filePath = filePath
        self._memory = memory
        self._vendor = vendor
        self._in_memory_node_b = in_memory_node_b
        self.run()

    def run(self):
        context = iter(etree.iterparse(self._filePath, events=('start', 'end')))
        # get root element
        _, root = next(context)

        SubNetwork = list()
        MeContext = ''
        ManagedElement = ''
        tag = ['SubNetwork', 'MeContext', 'ManagedElement', 'vsDataManagedElement', 'vsDataUtranCell',
               'vsDataGeranCell', "VsDataContainer"]

        in_nodeb_level = False
        in_utrancell_level = False
        nodeb_to_update = None

        VsDataContainer = ''

        if isinstance(tag, list):
            multi = True
        else:
            multi = False

        namespace = None
        for event, elem in context:
            if multi:
                if "}" in elem.tag:
                    namespace = elem.tag.split("}")[0].strip("{")
                    namespace = "{" + namespace + "}"
                else:
                    namespace = ""
                if event == 'start':
                    if elem.tag == namespace + 'SubNetwork':
                        SubNetwork.append(elem.get('id'))
                        elem.clear()

                    elif elem.tag == namespace + 'MeContext':
                        MeContext = elem.get('id')
                        elem.clear()

                    elif elem.tag == namespace + 'ManagedElement':
                        try:
                            ManagedElement = elem.find('attributes').find('userLabel').text
                        except:
                            ManagedElement = elem.get('id')
                        elem.clear()

                    elif elem.tag == namespace + 'vsDataManagedElement' and ManagedElement == '':
                        try:
                            ManagedElement = elem.find('logicalName').text
                        except:
                            try:
                                ManagedElement = elem.find('site').text
                            except:
                                pass
                        elem.clear()

                    elif elem.tag == namespace + 'VsDataContainer':
                        VsDataContainer = elem.get('id')
                        elem.clear()

                    elif elem.tag == namespace + 'vsDataUtranCell':
                        try:
                            if VsDataContainer != '':
                                nodeb_name = VsDataContainer[:-1]
                                cell_name = VsDataContainer
                                rnc_name = MeContext
                                in_utrancell_level = True
                                
                                # NODEB doesn't exist in memory
                                if nodeb_name not in self._memory:
                                    self._memory[nodeb_name] = dict()
                                    self._memory[nodeb_name]['RNC_NAME'] = rnc_name
                                    self._memory[nodeb_name]['CELL_NAMES'] = list()
                                    self._memory[nodeb_name]['CELL_PAIRS'] = dict()

                                # check if RNC_NAME has been updated
                                elif self._memory[nodeb_name]['RNC_NAME'] != rnc_name:
                                    self._memory[nodeb_name]['RNC_NAME'] = rnc_name
                                
                                for key in self._memory.keys():
                                    if cell_name in self._memory[key]['CELL_NAMES']:
                                        nodeb_to_update = key
                                        if 'CELL_PAIRS' not in self._memory[nodeb_to_update]:
                                            self._memory[nodeb_to_update]['CELL_PAIRS'] = dict()
                                        self._memory[nodeb_to_update]['CELL_PAIRS'][cell_name] = -1
                                        break
                                else:
                                    self._memory[nodeb_name]['CELL_NAMES'].append(cell_name)
                                    if 'CELL_PAIRS' not in self._memory[nodeb_name]:
                                        self._memory[nodeb_name]['CELL_PAIRS'] = dict()
                                    self._memory[nodeb_name]['CELL_PAIRS'][cell_name] = -1

                        except Exception as er:
                            print(er)
                        elem.clear()

                    elif elem.tag == namespace + 'vsDataRbsLocalCell' or elem.tag == namespace + 'vsDataNodeBLocalCell':
                        in_nodeb_level = True
                        nodeb_name = MeContext
                        # NODEB not exist in dictionary of nodeb names and their associated RNC/cell ID pairs
                        if nodeb_name not in self._in_memory_node_b:
                            self._in_memory_node_b[nodeb_name] = list()
                        elem.clear()

                    elif elem.tag == namespace + 'vsDataGeranCell':
                        try:
                            if VsDataContainer != '':
                                nodeb_name = VsDataContainer[:-1]
                                if nodeb_name not in self._memory:
                                    self._memory[nodeb_name] = dict()
                                    self._memory[nodeb_name]['BSC_NAME'] = MeContext
                                    self._memory[nodeb_name]['CELL_NAMES'] = list()

                                if VsDataContainer not in self._memory[nodeb_name]['CELL_NAMES']:
                                    self._memory[nodeb_name]['CELL_NAMES'].append(VsDataContainer)
                        except Exception as er:
                            print(er)
                        elem.clear()

                elif event == 'end':
                    if elem.tag == namespace + 'SubNetwork':
                        SubNetwork.pop(0)
                        elem.clear()
                    elif elem.tag == namespace + 'MeContext':
                        MeContext = ''
                        elem.clear()

                    elif elem.tag == namespace + "localCellId":
                        if VsDataContainer != '':
                            valueLocalCellId = elem.text
                            cell_id = valueLocalCellId
                            
                            if in_nodeb_level:
                                in_nodeb_level = False
                                nodeb_name = MeContext
                                rnc_name = SubNetwork[-1]
                                if [rnc_name, cell_id] not in self._in_memory_node_b[nodeb_name]:
                                    self._in_memory_node_b[nodeb_name].append([rnc_name, cell_id])
                                
                            elif in_utrancell_level:
                                in_utrancell_level = False
                                cell_name = VsDataContainer
                                rnc_name = MeContext
                                if nodeb_to_update is not None:
                                    self._memory[nodeb_to_update]['CELL_PAIRS'][cell_name] = cell_id
                                    nodeb_to_update = None
                                else:
                                    nodeb_name = cell_name[:-1]
                                    self._memory[nodeb_name]['CELL_PAIRS'][cell_name] = cell_id
            else:
                elem.clear()
        del context
    
    
def update_nodeb_by_cell_id(new_node_b_data, memory):
    """
    Re-maps cell names to the correct nodeb based on nodeb files, if rnc name and cell id is matched.
    Since rnc name is not available in all nodeb files, it is fetched from the config directly, thus only cell ids
    that exist in rnc file and nodeb files will be updated, if the nodeb does not follow the [:-1] rule.
    Args:
    - new_node_b_data (dict): Dictionary of nodeb names and their associated cell ids, from nodeb files.
    - memory (dict): Dictionary used for storing characterization data.
    Returns:
    - final_memory (dict): Dictionary with updated data.
    """
    final_memory = {}
    
    # re-map in_memory_node_b data to include RNC_NAME from memory
    for node_b, rnc_cell_list in new_node_b_data.items():
        if node_b in memory:
            new_node_b_data[node_b] = {memory[node_b]['RNC_NAME']: list(set(pair[1] for pair in rnc_cell_list))}
        else:
            rnc = list(set(pair[0] for pair in rnc_cell_list))
            rnc = rnc[0] if len(rnc) == 1 else ''  # '' if more than one rnc was registered above this nodeb - incorrect
            new_node_b_data[node_b] = {rnc: list(set(pair[1] for pair in rnc_cell_list))}
        
    # iterate memory data to build a correct memory based on in_memory_node_b data:
    for node_b, values in memory.items():
        rnc_name = values['RNC_NAME']
        if node_b not in final_memory:
            final_memory[node_b] = {'RNC_NAME': rnc_name, 'CELL_NAMES': []}
            
        if 'CELL_PAIRS' not in values:
            # no data in current files to change any of these cell_names
            final_memory[node_b]['CELL_NAMES'].extend(values['CELL_NAMES'])
            continue
        
        for cell_name in values['CELL_NAMES']:
            cell_id = values['CELL_PAIRS'].get(cell_name, None)
            
            if cell_id is None:
                # no data in new files to change this particular cell_name
                final_memory[node_b]['CELL_NAMES'].append(cell_name)
                continue
                
            for node_b_2, rnc_cell_list in new_node_b_data.items():
                if rnc_name in rnc_cell_list and cell_id in rnc_cell_list[rnc_name]:
                    # true if pair rnc/cell_id exists in new data; nodeb can be the same or different
                    if node_b_2 not in final_memory:
                        final_memory[node_b_2] = {'RNC_NAME': rnc_name, 'CELL_NAMES': []}
                    final_memory[node_b_2]['CELL_NAMES'].append(cell_name)
                    break
            else:
                final_memory[node_b]['CELL_NAMES'].append(cell_name)
    
    return final_memory


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Enrich Ericsson Parameter files.')
    parser.add_argument('-indir', help='the input directory')
    parser.add_argument('-outdir', help='the output directory')
    parser.add_argument('-ip', help='ip')
    parser.add_argument('-vendor', help='vendor')
    args = parser.parse_args()

    in_memory_node_b = dict()

    if not os.path.exists(args.indir):
        print('[Critical] Input directory doesnt exist: {0}'.format(args.indir))
        sys.exit()

    if not os.path.exists(args.outdir):
        print('[Critical] Output directory doesnt exist: {0}'.format(args.outdir))
        sys.exit()

    # Loads the previous network tree dictionary
    try:
        network_tree_filename = "config_{0}.json".format(args.ip)
        inMemory = dict(json.load(open(os.path.join(args.outdir, network_tree_filename), 'r')))
    except IOError:
        # File does not exist yet
        inMemory = dict()

    startTime = datetime.datetime.now()
    print("------------------------------------------------------------------------------------")
    print("--------- SCRIPT START              -----> {0}  ---------".format(str(startTime)))
    print("--------- IN DIRECTORY: {:51} ---------".format(args.indir))
    print("--------- OUTPUT DIRECTORY: {:47} ---------".format(args.outdir))
    print("------------------------------------------------------------------------------------")

    filesToProcess = [args.indir + f for f in os.listdir(args.indir) if os.path.isfile(args.indir + f)]
    for fileName in filesToProcess:
        if not fileName.endswith('xml'):
            print('[Warning] File type unknown: {0}'.format(os.path.basename(fileName)))
            continue

        print("----- START_PROCESSING_FILE: {:30s}  TIME: {:s} -".format(os.path.basename(fileName),
                                                                          str(datetime.datetime.now())))
        try:
            EricssonEnrichParameter(fileName, inMemory, in_memory_node_b, args.vendor)
        except Exception as e:
            print('[Error] Exception in file {0}: {1}'.format(os.path.basename(fileName), e))

    inMemory = update_nodeb_by_cell_id(in_memory_node_b, inMemory)
    
    # clear keys with empty cell names
    inMemory = {key: value for key, value in inMemory.items() if value['CELL_NAMES']}

    f = open('{0}{1}config_{2}.json'.format(args.outdir, ('' if args.outdir.endswith('/') else '/'), args.ip), 'w')
    f.write(json.dumps(inMemory))
    f.close()
    endTime = datetime.datetime.now()
    print("------------------------------------------------------------------------------------")
    print("--------- SCRIPT END                    -----> {0}  ---------".format(str(endTime)))
    print("--------- TOTAL DURATION                 ----->   {0}       ---------".format(endTime - startTime))
    print("------------------------------------------------------------------------------------")
