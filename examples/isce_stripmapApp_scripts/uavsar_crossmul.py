#!/usr/bin/env python3


import isce
import os
import logging
from components.stdproc.stdproc import crossmul
import isceobj
from iscesys.ImageUtil.ImageUtil import ImageUtil as IU
import isceobj
import argparse
import glob

def createParser():

    '''
    Command Line Parser.
    '''
    parser = argparse.ArgumentParser( description='Generate offset field between two Sentinel swaths')
    parser.add_argument('-s', '--slc_dir', type=str, dest='slcDir', required=True,
            help='Directory with all SLC subdirectories')
    parser.add_argument('-n', '--num_connections', type=int, dest='numConnections', default=1,
            help='Directory with all SLC subdirectories')
    parser.add_argument('-o', '--outdir', type=str, dest='outDir', default='crossmul',
            help='Prefix of output int and amp files')
    parser.add_argument('-a', '--alks', type=int, dest='azlooks', default=1,
            help='Azimuth looks')
    parser.add_argument('-r', '--rlks', type=int, dest='rglooks', default=1,
            help='Range looks')

    return parser

def cmdLineParse(iargs = None):
    parser = createParser()
    return parser.parse_args(args=iargs)

def run(imageSlc1, imageSlc2, resampName, azLooks, rgLooks):
    objSlc1 = isceobj.createSlcImage()
    IU.copyAttributes(imageSlc1, objSlc1)
    objSlc1.setAccessMode('read')
    objSlc1.createImage()

    objSlc2 = isceobj.createSlcImage()
    IU.copyAttributes(imageSlc2, objSlc2)
    objSlc2.setAccessMode('read')
    objSlc2.createImage()

    slcWidth = imageSlc1.getWidth()
    intWidth = int(slcWidth / rgLooks)

    lines = min(imageSlc1.getLength(), imageSlc2.getLength())

    resampAmp = resampName + '.amp'
    resampInt = resampName + '.int'

    objInt = isceobj.createIntImage()
    objInt.setFilename(resampInt)
    objInt.setWidth(intWidth)
    imageInt = isceobj.createIntImage()
    IU.copyAttributes(objInt, imageInt)
    objInt.setAccessMode('write')
    objInt.createImage()

    objAmp = isceobj.createAmpImage()
    objAmp.setFilename(resampAmp)
    objAmp.setWidth(intWidth)
    imageAmp = isceobj.createAmpImage()
    IU.copyAttributes(objAmp, imageAmp)
    objAmp.setAccessMode('write')
    objAmp.createImage()

    objCrossmul = crossmul.createcrossmul()
    objCrossmul.width = slcWidth
    objCrossmul.length = lines
    objCrossmul.LooksDown = azLooks
    objCrossmul.LooksAcross = rgLooks

    objCrossmul.crossmul(objSlc1, objSlc2, objInt, objAmp)

    for obj in [objInt, objAmp, objSlc1, objSlc2]:
        obj.finalizeImage()

    return imageInt, imageAmp


def igram_pair(master, slave, output, azlooks, rglooks):

    img1 = isceobj.createImage()
    img1.load(master + '.xml')

    img2 = isceobj.createImage()
    img2.load(slave + '.xml')

    if not os.path.exists(os.path.dirname(output)):
       os.makedirs(os.path.dirname(output))

    run(img1, img2, output, azlooks, rglooks)

def estCoherence(outfile, corfile):
    from mroipac.icu.Icu import Icu

    #Create phase sigma correlation file here
    filtImage = isceobj.createIntImage()
    filtImage.load( outfile + '.xml')
    filtImage.setAccessMode('read')
    filtImage.createImage()

    phsigImage = isceobj.createImage()
    phsigImage.dataType='FLOAT'
    phsigImage.bands = 1
    phsigImage.setWidth(filtImage.getWidth())
    phsigImage.setFilename(corfile)
    phsigImage.setAccessMode('write')
    phsigImage.createImage()


    icuObj = Icu(name='uavsar_filter_icu')
    icuObj.configure()
    icuObj.unwrappingFlag = False
    icuObj.useAmplitudeFlag = False

    icuObj.icu(intImage = filtImage,  phsigImage=phsigImage)
    phsigImage.renderHdr()

    filtImage.finalizeImage()
    phsigImage.finalizeImage()

def get_dates(slcDir):

    slcDirs = glob.glob(slcDir+"*")
    dateList = []
    for dd in slcDirs:
        dateList.append(os.path.basename(dd))

    dateList.sort()
    return dateList

def main(iargs=None):

    inps = cmdLineParse(iargs)
    dateList = get_dates(inps.slcDir)

    for ii,dd in enumerate(dateList):
        masterDate = dd
        slcs = glob.glob(os.path.join(inps.slcDir, masterDate , "*.slc"))
        if len(slcs) > 0:
           masterSlc = slcs[0]
        else:
           continue

        for jj in range(ii+1, ii+1+inps.numConnections):
            if jj < len(dateList):
              slaveDate = dateList[jj]

              slcs = glob.glob(os.path.join(inps.slcDir, slaveDate , "*.slc"))
              if len(slcs) > 0:
                  slaveSlc = slcs[0]
              else:
                  continue

              ifgramName = os.path.join(inps.outDir, masterDate + "_" + slaveDate , masterDate + "_" + slaveDate)
              print("generating  " + ifgramName)
              igram_pair(masterSlc, slaveSlc, ifgramName, inps.azlooks, inps.rglooks)

              print("estimate coherence")
              estCoherence(ifgramName+".int", ifgramName+".coh")

if __name__ == '__main__':

    main()

    '''
    Main driver.
    '''
