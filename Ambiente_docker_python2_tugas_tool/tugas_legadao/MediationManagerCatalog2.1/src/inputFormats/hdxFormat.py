__doc__ = \
	__version__ = '1.1'
__authors__ = ['Version 0.1: Bruno Silva <bruno-e-silva@alticelabs.com>']

import lxml.html as html
from lib.functions import xmlReader
from BeautifulSoup import BeautifulSoup
import re
import os
from lib.Logger import Logger

def getRoot(path, file):
	badHtml = (open(path + file, 'r')).read()
	soup = BeautifulSoup(badHtml)
	return html.fromstring(soup.prettify())

def readHDXFile(tech, info, path):
	logger = Logger('hdx').get()
	#path = 'C:\Users\withus\Desktop\Demandas\2019\HUAWEI\HUAWEI_U2000_NGN_PM_MSoftX3000\English\libraries\resources\'
	flag = False
	# 1. gets info by tech
	if os.path.exists(path + 'statistic.html'):
		data = getBlock(path, 'statistic.html')
		# 2. Gets 1 Level Group names
		data = getBlock(path, data[tech])
		# 3. For Family group get Families inside
		familiePath = dict()
		for key in data.keys():
			familiePath.update(getBlock(path, data[key]))
	else:
		familiePath = getBlockXML(path, 'navi.xml')
		flag = True

	for ossId in info.keys():
		nameId = re.sub(r'\n|\r| |\t', '', info[ossId]['attributes']['name'])
		if nameId in familiePath.keys():
			info[ossId] = getFamilieInfo(path, familiePath[nameId], info[ossId], flag)
		elif nameId.upper() in familiePath.keys():
			info[ossId] = getFamilieInfo(path, familiePath[nameId.upper()], info[ossId], flag)
		else:
			for fam in familiePath.keys():
				info[ossId] = getFamilieInfo(path, familiePath[fam], info[ossId], flag)
			logger.warning(('Couldn\'t find familie {:10s}').format(ossId))
	return info

def getFamilieInfo(path, fileName, info, flag):
	reItemId = re.compile(r'^(.+?)( |$)')
	logger = Logger('hdx').get()
	root = getRoot(path, fileName)
	for body in root.findall('body'):
		try:
			if flag:
				p = body.find('p')
				if p is None:
					p = (body.find('div')).find('p')
				desc = re.sub(r'\n|\r| |\t', ' ', p.text)
				if re.sub(r' ', '', desc) != '':
					info['attributes']['desc'] = desc
				else:
					flag = False
		except:
			pass
		for div in body.findall('div'):
			if not flag:
				for div2 in div.findall('div'):
					if div2.get('class') == 'section':
						sectionType = re.sub(r'\n|\r| |\t', '', ((div2.find('h4')).find('a').text))
						if re.search(r'(Description(s*))|(Definition(s*))|(Meaning(s*))', sectionType) is not None:
							p = div2.find('p')
							if p is None:
								p = div2.find('div')
							else:
								span = p.find('span')
								if span is not None:
									info['attributes']['desc'] = re.sub(r'\n|\r| |\t', ' ', span.text)
							info['attributes']['desc'] = info['attributes']['desc'] + re.sub(r'\n|\r| |\t', ' ', p.text)
					else:
						p = div2
						tbody = div2.find('table')
						if tbody is not None:
							tbody = tbody.find('tbody')
							if tbody is not None:
								try:
									tr = tbody.find('tr')
									td = tr.findall('td')
									if re.search(r'(Description(s*))|(Definition(s*))|(Meaning(s*))', (((td[0]).find('p')).find('strong')).text):
										p = td[1].find('div')
								except:
									pass
						if p is not None:
							info['attributes']['desc'] = info['attributes']['desc'] + re.sub(r'\n|\r| |\t', ' ', p.text)
			ul = div.find('ul')
			if ul is not None:
				try:
					for li in ul.findall('li'):
						a = li.find('strong').find('a')
						itemIdFull = re.sub(r'\n|\r|\t', '', a.text)
						itemId = re.search(r'(\d+?) \w.*', itemIdFull)
						if itemId is not None:
							itemId = itemId.group(1)
							if itemId in info['items'].keys():
								try:
									info['items'][itemId] = getItemInfo(path, re.sub(r'(\.\./\.\./)', '', a.get('href')), info['items'][itemId])
								except:
									logger.warning('Couldn\'t get description of item ' + itemId)
						else:
							itemIdFull = re.sub(r' ', '', itemIdFull).upper()
							found = False
							for key in info['items'].keys():
								if itemIdFull == re.sub(r' ', '', info['items'][key]['name']).upper():
									try:
										info['items'][key] = getItemInfo(path, re.sub(r'(\.\./\.\./)', '', a.get('href')), info['items'][key])
										found = True
									except:
										logger.warning('Couldn\'t get description of item ' + key)
								elif itemIdFull == re.sub(r'(\(.+?\)$)| ', '', info['items'][key]['name']).upper():
									try:
										info['items'][key] = getItemInfo(path, re.sub(r'(\.\./\.\./)', '', a.get('href')), info['items'][key])
										found = True
									except:
										logger.warning('Couldn\'t get description of item ' + key)
							if not found:
								logger.warning('Name of item ' + itemIdFull + ' was edited.')
								itemIdFull = re.sub(r'\(.+?\)$', '', itemIdFull)
								for key in info['items'].keys():
									if itemIdFull == re.sub(r' ', '', info['items'][key]['name']).upper():
										try:
											info['items'][key] = getItemInfo(path, re.sub(r'(\.\./\.\./)', '', a.get('href')), info['items'][key])
											found = True
										except:
											logger.warning('Couldn\'t get description of item ' + key)
									elif itemIdFull == re.sub(r'(\(.+?\)$)| ', '', info['items'][key]['name']).upper():
										try:
											info['items'][key] = getItemInfo(path, re.sub(r'(\.\./\.\./)', '', a.get('href')), info['items'][key])
											found = True
										except:
											logger.warning('Couldn\'t get description of item ' + key)
				except:
					if ul.get('class') == 'ullinks':
						for dl in ul.findall('dt'):
							try:
								a = dl.find('a')
								itemId = re.match(reItemId, a.text)
								print itemId
								if itemId in info['items'].keys():
									info['items'][itemId] = getItemInfo(path, re.sub(r'(\.\./\.\./)', '', a.get('href')), info['items'][itemId])
							except:
								logger.warning('Couldn\'t get description of item')

	return info

def getItemInfo(path, fileName, info):
	root = getRoot(path, fileName)
	for body in root.findall('body'):
		for div in body.findall('div'):
			sectionType = ''


			for div2 in div.findall('div'):
				try:
					h2 = div2.find('h2')
					a = h2.find('a')
					sectionType = re.sub(r'\n|\r| |\t', '', a.text)
					if re.search(r'(Description(s*))|(Definition(s*))|(Meaning(s*))', sectionType) is not None:
						for div3 in div2.findall('div'):
							for p in div3.findall('p'):
								info['desc'] += p.text + ' '
						return info
				except:
					pass
				if div2.get('class') == 'section':
					sectionType = re.sub(r'\n|\r| |\t', '', ((div2.find('h4')).find('a').text))
					if re.search(r'(Description(s*))|(Definition(s*))|(Meaning(s*))', sectionType) is not None:
						p = div2.find('p')
						if p is None:
							p = div2.find('div')
						if p is None:
							p = div2
							p.text = re.sub(r'^.*([\s\S]*</h4>)', '', html.tostring(p))
						if p.text is not None:
							info['desc'] += re.sub(r'\n|\r| |\t', ' ', re.sub(r'(</div>)', '', p.text))

						if info['desc'] in ['', ' ']:
							info['desc'] += re.sub(r'([\s\S]<.+? >[\s\S])|([\s\S]< /.+? >[\s\S])|\n|\t|\r| ', ' ', html.tostring(div2))
						try:
							for p in div2.findall('p'):
								info['desc'] += ' ' + re.sub(r'\n|\r| |\t', ' ', re.sub(r'([\s\S]<.+? >[\s\S])|([\s\S]< /.+? >[\s\S])|\n|\t|\r| ', '', p.text))
						except:
							pass
						try:
							ul = div2.find('ul')
							if ul is not None:
								for li in ul.findall('li'):
									p = li.find('p')
									if p is not None:
										info['desc'] += ' ' + re.sub(r'\n|\r| |\t', ' ', p.text)
						except:
							pass
						return info
	return info

def getBlock(path, fileName):
	data = dict()
	root = getRoot(path, fileName)
	for body in root.findall('body'):
		for div in body.findall('div'):
			try:
				for li in (div.find('ul')).findall('li'):
					a = li.find('strong').find('a')
					data[re.sub(r'\r|\n|\t| ', '', a.text.upper())] = re.sub(r'(\.\.\/\.\.\/)', '', a.get('href'))
			except:
				pass
	return data

def getBlockXML(path, fileName):
	data = dict()
	root = xmlReader(path + fileName)
	for t1 in root.findall('topic'):
		if t1.get('txt') == 'References':
			for t2 in t1.findall('topic'):
				if t2.get('txt') == 'Counters':
					for t3 in t2.findall('topic'):
						for t4 in t3.findall('topic'):
							data[re.sub(r'\r|\n|\t| ', '', t4.get('txt').upper())] = re.sub(r'(\.\.\/\.\.\/)', '', t4.get('url'))
	return data