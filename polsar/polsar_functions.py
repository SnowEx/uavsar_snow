"""
https://dges.carleton.ca/courses/IntroSAR/Winter2019/SECTION%203%20-%20Carleton%20SAR%20Training%20-%20SAR%20Polarimetry%20%20-%20Final.pdf

Danish paper DOI: 10.1109/LGRS.2022.3169994
"""

import numpy as np
from glob import glob
from os.path import join, basename
from uavsar_pytools.convert.tiff_conversion import read_annotation


def get_polsar_stack(in_dir):
    """
    Reads UAVSAR GRD files from input directory.

    Arguments
    ---------
    in_dir : str
        Input directory that contains UAVSAR GRD data. Must have all 
        crosspruducts (HHHH, HVHV, VVVV, HHHV, HVHV, and HVVV) and the 
        associated .ann file.
    
    Returns
    -------
    stack : np.array
        Array of size [n x m x 6] containing UAVSAR data
    """
    # Read ann file
    ann_fp = glob(join(in_dir, '*.ann'))[0]
    desc = read_annotation(ann_fp)
    nrows = desc['grd_pwr.set_rows']['value']
    ncols = desc['grd_pwr.set_cols']['value']
    fps = glob(join(in_dir, '*.grd'))
    # Read GRD files
    pol = {}
    for f in fps:
        name = basename(f).split('_')[-3][4:]
        # Complex variables
        if name == 'HVVV' or name == 'HHHV' or name == 'HHVV':
            arr = np.fromfile(f, dtype = np.complex64).reshape(nrows, ncols)
        # Real variables
        else:
            arr = np.fromfile(f, dtype = np.float32).reshape(nrows, ncols)
        
        arr[arr == 0] = np.nan
        pol[name] = arr
        stack = np.dstack([pol['HHHH'], pol['HHHV'], pol['HVHV'], pol['HVVV'], pol['HHVV'], pol['VVVV']])
        
        return stack


def calc_C3():
    """

    """


def C3_to_T3():
    """
    https://github.com/EO-College/polsarpro/blob/master/Soft/src/lib/util_convert.c
    use more readable version
    """

def T3_to_alpha1():
    """
    
    """


def T3_to_mean_alpha():
    """
    
    """


def uavsar_alpha1():
    """
    
    """


def uavsar_meanalpha():
    """
    
    """


def uavsar_H():
    """"
    entropy
    """


def uavsar_A():
    """
    anisotropy
    """