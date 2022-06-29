#!/usr/bin/env python3

############################################################
# Script to generate UAVSAR ifgs xmls and vrts using isce. #
# Author: Talib Oliver, 2021                               #
############################################################

import os
import glob
import argparse
import json
import isce
import isceobj
from isceobj.Util.decorators import use_api
# from iscesys import DateTimeUtil as DTU
from iscesys.ImageUtil.ImageUtil import ImageUtil as IU

def createParser():
    '''
    Create command line parser.
    '''

    parser = argparse.ArgumentParser(description='Generate vrt and xml for UAVSAR')
    parser.add_argument('-i', '--input', dest='ifgdir', type=str, required=True,
            help='ifgram directory.')
    return parser


def cmdLineParse(iargs=None):
    '''
    Command line parser.
    '''

    parser = createParser()
    return parser.parse_args(args = iargs)


def run(ifg, amp, cor, samples):
    int_file = ifg[0]
    amp_file = amp[0]
    cor_file = cor[0]

    outInt = isceobj.Image.createIntImage()
    outInt.setFilename(int_file)
    outInt.setWidth(samples)
    outInt.setAccessMode('read')
    outInt.renderHdr()
    outInt.renderVRT()

    outAmp = isceobj.Image.createAmpImage()
    outAmp.setFilename(amp_file)
    outAmp.setWidth(samples)
    outAmp.setAccessMode('read')
    outAmp.renderHdr()
    outAmp.renderVRT()

    outCor = isceobj.Image.createImage()
    outCor.setFilename(cor_file)
    outCor.setWidth(samples)
    outCor.setAccessMode('read')
    outCor.setDataType('FLOAT')
    outCor.renderHdr()
    outCor.renderVRT()


def main(iargs=None):

    inps = cmdLineParse(iargs)
    int_json = os.path.join(inps.ifgdir, 'int.json')
    with open(int_json) as fp:
        int_info = json.load(fp)
    int_info_keys = list(int_info.keys())   
    samples_int = int_info['samples_int']
    dirs = glob.glob(inps.ifgdir+'/20*')
    dateList = []
    for dir in dirs:
        dateList.append(os.path.basename(dir))
        ifg = glob.glob(dir+'/*.int')
        amp = glob.glob(dir+'/*.amp')
        cor = glob.glob(dir+'/*.cor')
        run(ifg, amp, cor, samples_int)

if __name__ == '__main__':

    main() 
 
    '''
    Main driver.
    '''
