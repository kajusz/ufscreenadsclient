#!/usr/bin/env python3

import logging
logger = logging.getLogger(__name__)

import os
import sys

import tempfile
import urllib.request
import time
import shutil
import xml.etree.ElementTree as ET

def contentProviderArgParseSetup(parser):
    parser.add_argument('-t', '--target', dest='target', type=int, help='Set the target playlist')
    parser.add_argument('-l', '--list-targets', action='store_true', help='List available targets')
    parser.add_argument('--dummy', action='store_true', help='Generate dummy files for offline testing')

def contentProviderArgParseParse(args, params):
    if (args.target != None):
        assert(args.target > 0)
        params['target'] = args.target
    else:
        logger.debug('No target specified, using target 1.')
    print('Using target', params['target'])

    ### Create dummy files
    if args.dummy:
        createDummyFiles(params['cacheDir'])

    ### List display targets
    if args.list_targets:
        printTargets(fetchTargets(params['cacheDir'], params['apiEndpoint']))
        sys.exit(0)

    ### List display items
    count = printList(fetchListData(params['target'], params['cacheDir'], params['apiEndpoint']))
    if count == 0:
        logger.error('Target has no content')
        sys.exit(1)
        ### TODO check if target exists

    return None

class ufContentProvider():
    def __init__(self, params):
        self.params = params
        self.cacheDir = self.params['cacheDir']
        self.apiEndpoint = self.params['apiEndpoint']

        self.apiListEndpoint = self.apiEndpoint + 'list/' + str(self.params['target'])
        self.apiImageEndpoint = self.apiEndpoint + 'image/'
        self.apiVideoEndpoint = self.apiEndpoint + 'video/'

        self.listOfAds = []

    def _getExt(self, adId):
        tree = ET.parse(os.path.join(self.cacheDir, self.listXmlName()))
        treeroot = tree.getroot()
        for screenAd in treeroot.iter("ScreenAd"):
            if (adId == screenAd.attrib["ID"]):
                adType = screenAd.attrib["Type"]
                if (adType == "Image"):
                    return ".jpg"
                elif (adType == "Video"):
                    return ".mp4"
                else:
                    return None
        print("Error: Id not found")

    def _getFileName(self, adType, adId):
        if (adType == "Image"):
            return str(adId) + ".jpg"
        elif (adType == "Video"):
            return str(adId) + ".mp4"
        else:
            return None

    def _getEndpUrl(self, adType, adId):
        if (adType == "Image"):
            return self.apiImageEndpoint + adId
        elif (adType == "Video"):
            return self.apiVideoEndpoint + adId
        else:
            return None

    def listXmlName(self):
        return 'list' + str(self.params['target']) + '.xml'

    def target(self, target):
        self.params['target'] = target

    def load(self):
        fetchList = []
        newListOfAds = []

### todo, this doesn't need to be called here???
        downloadXml(self.apiListEndpoint, self.listXmlName(), self.cacheDir)

        haveTheseImagesSoFar = []
        for root, dirs, files in os.walk(self.cacheDir, topdown=True):
            for lfile in sorted(files):
                if lfile.endswith(('jpg', 'mp4')):
                    haveTheseImagesSoFar.append(os.path.basename(lfile))

        tree = ET.parse(os.path.join(self.cacheDir, self.listXmlName()))
        treeroot = tree.getroot()
        for screenAd in treeroot.iter("ScreenAd"):
            adId = screenAd.attrib["ID"]
            adType = screenAd.attrib["Type"]
            adDur = screenAd.attrib["Duration"]

            if (adType == "Image" or adType == "Video"):
                if not (self._getFileName(adType, adId) in haveTheseImagesSoFar):
                    fetchList.append(self._getEndpUrl(adType, adId))
                elif (time.mktime(time.strptime(screenAd.attrib["LastUpdated"], "%Y-%m-%d %H:%M:%S")) > os.path.getmtime(os.path.join(self.cacheDir, self._getFileName(adType, adId)))):
                    os.remove(os.path.join(self.cacheDir, self._getFileName(adType, adId)))
                    fetchList.append(self._getEndpUrl(adType, adId))
            else:
                logger.error("Web content not implemented")

            if adDur == "Short":
                duration = self.params['durShort']
            elif adDur == "Default":
                duration = self.params['durDefault']
            elif adDur == "Long":
                duration = self.params['durLong']
            else:
                duration = self.params['durDefault']

            newListOfAds.append({
                'id':adId,
                'type':adType,
                'description':screenAd.attrib["Description"],
                'duration':duration,
                'lastupdated':screenAd.attrib["LastUpdated"],
                'path':os.path.join(self.cacheDir, self._getFileName(adType, adId))
            })

        with tempfile.TemporaryDirectory() as tmpcacheDir:
            if fetchList:
                print('Need to download', len(fetchList), 'files...')
                dl = downloader(targetDir=tmpcacheDir)
                dl.queue(fetchList)
                dl.run()

            for root, dirs, files in os.walk(tmpcacheDir, topdown=True):
                for lfile in sorted(files):
                    shutil.copyfile(os.path.join(tmpcacheDir, lfile), os.path.join(self.cacheDir, lfile + self._getExt(lfile)))

        self.listOfAds = newListOfAds
        ### TODO, regenerate paths cache

    def refresh(self, dt=None):
        self.load()

    def listDetailed(self, idx=None):
        return self.list(idx)

    def list(self, idx=None):
        if (idx == -1):
            return len(self.listOfAds)
        elif (idx != None):
            return self.listOfAds[idx]

        return self.listOfAds

### tc.bp.web.downloader
class downloader():
    def __init__(self ,targetDir=None):
        import urllib.request
        import os

        self.targetDir = targetDir
        self.urlQueue = []

    def queue(self, urls):
        self.urlQueue.append(urls)

    def run(self, url=None, urls=None, target=None, targetDir=None, targetType="binary"):
        if (url != None and target != None):
            with urllib.request.urlopen(url) as f:
                with open(target, 'w+b') as g:
                    g.write(f.read())
            return

        if (urls != None):
            self.urlQueue.append(urls)

        if (targetDir != None):
            self.targetDir = targetDir

        for lnks in self.urlQueue:
            for lnk in lnks:
                logger.debug('Downloading %s', lnk)
                with urllib.request.urlopen(url=str(lnk)) as f:
                    with open(os.path.join(self.targetDir, lnk.rsplit('/', 1)[-1]), 'w+b') as g:
                        g.write(f.read())

def downloadXml(url, name, location):
    import tempfile
    import os
    import urllib.request
    import shutil

    with tempfile.NamedTemporaryFile(delete=False) as tmpXml:
        tmpXml.seek(0)

        xmlFile = os.path.join(location, name)
        xmlOldFile = os.path.join(location, name + '.old')

        try:
            with urllib.request.urlopen(url) as f:
                tmpXml.write(f.read())
#                with open(tmpXml.name, 'w+b') as g:
#                    g.write(f.read())
                tmpXml.flush()
                tmpXml.close()
        except urllib.error.URLError:
            if os.path.isfile(xmlFile):
                logger.warn('Using cached %s.xml', name)
            else:
                logger.error('Failed to download %s.xml and no cached file exists', name)
                sys.exit(1)
        else:
            if os.path.isfile(xmlOldFile):
                os.remove(xmlOldFile)
            if os.path.isfile(xmlFile):
                os.rename(xmlFile, xmlOldFile)

            shutil.copyfile(tmpXml.name, xmlFile)

        os.remove(tmpXml.name)

def createDummyFiles(dir):
    with open(os.path.join(dir, 'target.xml'), "w") as targetData:
        targetData.write('<?xml version="1.0"?><Targets><Target ID="1">Cinema</Target><Target ID="2">Hatch (During Films)</Target><Target ID="3">Hatch (General)</Target><Target ID="4">End of Film Special</Target><Target ID="7">Cinema (Marathons)</Target><Target ID="8">Phoenix PPT</Target></Targets>')
        targetData.close()

    with open(os.path.join(dir, 'list1.xml'), "w") as listData:
        listData.write('<?xml version="1.0"?><ScreenAds><ScreenAd ID="218" Type="Image" Description="Unsociable Media" Duration="Default" LastUpdated="2017-06-29 18:14:15"/><ScreenAd ID="524" Type="Image" Description="Hearing Loop" Duration="Default" LastUpdated="2017-06-29 18:14:34"/><ScreenAd ID="519" Type="Image" Description="Get Involved" Duration="Default" LastUpdated="2017-10-04 15:33:43"/><ScreenAd ID="525" Type="Image" Description="Premiere Pass" Duration="Default" LastUpdated="2017-10-11 17:21:50"/><ScreenAd ID="659" Type="Image" Description="Garbage Deadpool" Duration="Default" LastUpdated="2017-10-20 21:29:42"/><ScreenAd ID="660" Type="Image" Description="Shuffle Cap" Duration="Default" LastUpdated="2017-10-23 15:12:13"/><ScreenAd ID="696" Type="Image" Description="Regular Popcorn" Duration="Default" LastUpdated="2017-11-14 18:48:16"/><ScreenAd ID="697" Type="Image" Description="M&amp;Ms" Duration="Default" LastUpdated="2017-11-14 18:48:47"/><ScreenAd ID="698" Type="Image" Description="Drinks" Duration="Default" LastUpdated="2017-11-14 18:51:55"/></ScreenAds>')
        listData.close()

def fetchTargets(cacheDir, apiEndpoint):
    targetXml = 'target.xml'
    downloadXml(apiEndpoint + 'list', targetXml, cacheDir)
    targetXml = os.path.join(cacheDir, targetXml)
    tree = ET.parse(targetXml)
    treeroot = tree.getroot()

    targetsList = []
    for xTarget in treeroot.iter('Target'):
        targetsList.append({'ID':xTarget.attrib['ID'], 'Name':xTarget.text})
    return targetsList

def fetchListData(target, cacheDir, apiEndpoint):
    listXml = 'list' + str(target) + '.xml'
    downloadXml(apiEndpoint + 'list/' + str(target), listXml, cacheDir)
    listXml = os.path.join(cacheDir, listXml)
    tree = ET.parse(listXml)
    treeroot = tree.getroot()

    data = []
    for screenAd in treeroot.iter("ScreenAd"):
        data.append({'ID':screenAd.attrib['ID'], 'Type':screenAd.attrib['Type'], 'Description':screenAd.attrib['Description'], 'Duration':screenAd.attrib['Duration'], 'LastUpdated':screenAd.attrib['LastUpdated']})
    return data

def printTargets(targetsList):
    print('Available targets: ')
    for i, target in enumerate(targetsList):
        print('   Target', target['ID'], '-', target['Name'])

def printList(dataList):
    print('Available content of list: ')
    for i, screenAd in enumerate(dataList):
        print('   Ad', i+1, ': id =', screenAd['ID'], '| type =', screenAd['Type'], '| description =', screenAd['Description'], '| duration =', screenAd['Duration'], '| lastupdated', screenAd['LastUpdated'])
    return len(dataList)
