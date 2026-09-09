import xml.etree.cElementTree as etree
import os
import re
import importlib

BaseOperator = importlib.import_module("shelf.collectorprocess.operators.BaseOperator").BaseOperator
FamilyObject = importlib.import_module("shelf.collectorprocess.operators.FamilyObject").FamilyObject

class Operator(BaseOperator):

    def __init__(self, operationParams, baseObject={}):
        BaseOperator.__init__(self, operationParams, baseObject=baseObject)

    def process(self, familyObj=FamilyObject(), baseObject={}):
        for file_path in familyObj.getFiles():
            if os.path.getsize(file_path) == 0: 
                continue
            
            # Variaveis globais do arquivo e do bloco
            doc = {'LOCALDN': '', 'ELEMENTTYPE': ''}
            meas_types = []
            info_id = 'generic'
            duration = 0
            
            # iterparse usando apenas o evento 'end' processa o arquivo no fluxo, sem sobrecarregar a RAM
            for _, elem in etree.iterparse(file_path, events=('end',)):
                
                # Ignora o namespace dinamicamente (pega so a ultima parte da tag)
                tag = elem.tag.split('}')[-1] 
                
                if tag == 'fileSender':
                    doc['LOCALDN'] = elem.get('localDn', '')
                    doc['ELEMENTTYPE'] = elem.get('elementType', '')
                
                elif tag == 'measCollec':
                    # Pega "2023-01-11T06:45:00+02:00" e transforma direto em "2023-01-11 06:45:00"
                    doc['BEGINTIME'] = elem.get('beginTime', '')[:19].replace('T', ' ')
                
                elif tag == 'measInfo':
                    info_id = elem.get('measInfoId', 'generic')
                
                elif tag == 'granPeriod':
                    match = re.search(r'\d+', elem.get('duration', '0'))
                    duration = int(match.group()) if match else 0
                    doc['DURATION'] = duration
                    doc['ENDTIME'] = elem.get('endTime', '')[:19].replace('T', ' ')
                
                elif tag == 'measTypes':
                    meas_types = elem.text.split() if elem.text else []
                
                elif tag == 'measResults':
                    meas_results = elem.text.split() if elem.text else []
                
                elif tag == 'measValue':
                    # Fim do bloco measValue: temos dados suficientes para gerar o evento final
                    meas_obj = elem.get('measObjLdn', '').replace(', ', ',')
                    event_data = doc.copy()
                    
                    if doc['LOCALDN']:
                        event_data['MEASOBJLDN'] = doc['LOCALDN'] + ',' + meas_obj
                    else:
                        event_data['MEASOBJLDN'] = meas_obj
                        
                    # Junta os arrays: ['M145', 'M146'] e ['10', '20'] vira {'M145': '10', 'M146': '20'}
                    event_data.update(dict(zip(meas_types, meas_results)))
                    
                    # Dispara para o proximo processo do framework de mediacao
                    familyObj.clearDocuments()
                    familyObj.setUnitID(info_id)
                    
                    try:
                        data_time = FamilyObject.parseEnvelopeDataTime(doc.get('BEGINTIME', ''))
                    except Exception:
                        data_time = doc.get('BEGINTIME', '')
                        
                    familyObj.addDocument({
                        "dataTime": data_time,
                        "granularitySec": duration,
                        "data": event_data
                    })
                    self.nextOp(familyObj=familyObj, baseObject=baseObject)
                
                # Libera o bloco lido da memoria imediatamente
                elem.clear() 
                
        familyObj.clearFiles()