from requests import get
from zipfile import ZipFile
from io import BytesIO
from os import path, listdir
import xml.etree.ElementTree as etree
import xmltodict
url = 'http://www.pepper1.net/zwavedb/device/export/device_archive.zip'
thisdir = path.dirname(path.abspath(__file__))



def DownloadDB():
    try:
        Downloaded = get(url)
    except Exception as e:
        raise ValueError('unable to download from pepperdb')
    ZipFile(BytesIO(Downloaded.content)).extractall(thisdir)

def GetInfo(vid, ptype, pid):
    for item in listdir(thisdir):
        if vid[2:] + '-' + ptype[2:] + '-' + pid[2:] in item:
            DeviceFile = item
    else:
        raise ValueError('Unable to find the requested device')

    tree = etree.parse(DeviceFile)
    root = tree.getroot()

def GetBaseInfo(vid, ptype, pid):
    searchstring = vid[2:] + '-' + ptype[2:] + '-' + pid[2:]
    print(searchstring)
    for xmlfile in listdir(thisdir):
        if searchstring in xmlfile:
            with open(thisdir + '/' + xmlfile) as FP:
                fulldict = xmltodict.parse(FP.read())
                break
    
    if fulldict:
        ReturnDict = {}
        ReturnDict['BrandName'] =\
        fulldict['ZWaveDevice']['deviceDescription']['brandName']
        ReturnDict['ProductName'] =\
        fulldict['ZWaveDevice']['deviceDescription']['productName']

        return ReturnDict
    return False

def Classlist(vid, ptype, pid):
    searchstring = vid[2:] + '-' + ptype[2:] + '-' + pid[2:]
    for xmlfile in listdir(thisdir):
        if searchstring in xmlfile:
            with open(thisdir + '/' + xmlfile) as FP:
                fulldict = xmltodict.parse(FP.read())
                break

    if fulldict:
        ReturnList = []
        for x in fulldict['ZWaveDevice']['commandClasses']['commandClass']:
            ReturnList.append(x['@id'])

    return ReturnList


