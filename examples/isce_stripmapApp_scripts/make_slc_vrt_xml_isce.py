#!/usr/bin/env python3

############################################################
# Script to from UAVSAR SLC xmls and vrts using isce.      #
# Modified by Talib Oliver, 2021                           #
############################################################

usage = """
Usage: make_slc_vrt_xml_isce.py directory [outfile]

Generate ISCE-like metadata files for the SLCs. 
This script uses ISCE libraries to generate vrt, xml and shelve files 
corresponding to the SLC infomation.

"""

import json
import os
import re
import sys
import glob
import isce
import isceobj
import shelve 
from isceobj.Util.decorators import use_api
from iscesys import DateTimeUtil as DTU


def get_slc_size(ann,seg_num=1):
    """Figure out number of SLC samples (columns) given its annotation file.
    """
    n = None
    m = None
    # Ad-hoc parser, sorry.
    with open(ann) as f:
        for line in f:
            if line.startswith('slc_{a}_1x1 Columns'.format(a=seg_num)):
                n = int(line.split('=')[1].split()[0])
            if line.startswith('slc_{a}_1x1 Rows'.format(a=seg_num)):
                m = int(line.split('=')[1].split()[0])
    if n  is None:
        raise IOError('Could not find SLC columns in annotation file.')
    return n,m

def write_xml(slcFile, samples, lines):
 
    length = lines 
    width = samples

    print (width,length)

    slc = isceobj.createSlcImage()
    slc.setWidth(width)
    slc.setLength(length)
    slc.filename = slcFile
    slc.setAccessMode('write')
    slc.renderHdr()
    slc.renderVRT()

def main(argv):
    if len(argv) < 2:
        print (usage)
        sys.exit(1)
    dir = argv[1]
    outfile = sys.stdout
    if len(argv) > 2:
        outfile = open(argv[2], 'w')

    #### Modified by TO starting here
    # Check for doppler file
    dopFile = glob.glob(dir+'/*.dop')
    if not os.path.exists(dopFile[0]):
        print ('Doppler file not found, please copy it to the work directory')
        sys.exit(1)
    images_json = os.path.join(dir, 'images.json')
    with open(images_json) as fp:
        images = json.load(fp)
    # Number of samples should be the same for all SLCs in the stack.
    id = list(images.keys())[0] #### Modified for Python 3
    slc_list = list(images.keys())
    # create shelve folder
    for a in slc_list:
        slc_path = os.path.join(dir, a) 
        if not os.path.exists(slc_path):
            os.mkdir(slc_path)
        segs = sorted(images[a]['segments'], key=int)
        slc_group = images[a]['segments']
        total_segs = len(segs)
        annFile = images[a]['annotation']
        cummulative_m = 0

        for seg in segs:
            n,m = get_slc_size(images[id]['annotation'],seg)
            slc_file = slc_group[seg]
            cummulative_m = cummulative_m + m
            write_xml(slc_file,n,m)

        cmd = 'unpackFrame_UAVSAR_JPLcode.py -i ' + annFile  + ' -d '+ dopFile[0] + ' -l '+ str(cummulative_m) + ' -o ' + slc_path 
        print (cmd)
        os.system(cmd)


if __name__ == '__main__':
    main(sys.argv)
