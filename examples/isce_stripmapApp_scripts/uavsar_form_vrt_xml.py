#!/usr/bin/env python3
############################################################
# Script to concatenate UAVSAR segmets for isce processing.#
# Author: Talib Oliver, 2021                               #
############################################################

import os
import argparse
import isce
import isceobj
import shelve

## Set paths to data
work_dir = os.path.expanduser('/Users/cabrera/Documents/Projects/Deltax/Processing/eterre_27309_210412')
os.chdir(work_dir)
print('Go to directory:', work_dir)
shelveFile = os.path.join(work_dir, 'SLC_seg1/20210402T2258/data')
slcFile = os.path.join(work_dir, 'SLC_merged/20210402T2258/20210402T2258.slc')
length, width = 144847, 9900

def createParser():
    '''
    Create command line parser.
    '''

    parser = argparse.ArgumentParser(description='Generate vrt and xml for UAVSAR')
    parser.add_argument('-s1', '--slc_seg1', dest='slc_seg1_dir', type=str, required=True,
            help='ifgram directory.')
    parser.add_argument('-s2', '--slc_seg2', dest='slc_seg2_dir', type=str, required=True,
            help='ifgram directory.')
    parser.add_argument('-o', '--slc_out', dest='slc_merged_dir', type=str, required=True,
            help='ifgram directory.')
    return parser


def cmdLineParse(iargs=None):
    '''
    Command line parser.
    '''

    parser = createParser()
    return parser.parse_args(args = iargs)

def write_xml(shelveFile, slcFile, length, width):
    with shelve.open(shelveFile,flag='r') as db:
        frame = db['frame']

    # length = frame.numberOfLines
    # width = frame.numberOfSamples

    print (frame) ## To test
    print (width,length)

    slc = isceobj.createSlcImage()
    slc.setWidth(width)
    slc.setLength(length)
    slc.filename = slcFile
    slc.setAccessMode('write')
    slc.renderHdr()
    slc.renderVRT()

write_xml(shelveFile, slcFile, length, width)
