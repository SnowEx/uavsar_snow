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
        Array of size [n x m x 6] containing UAVSAR data.
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


def calc_C3(HHHH, HHHV, HVHV, HVVV, HHVV, VVVV):
    """
    Calculates covariance matrix C3 from individual UAVSAR pixel locations. 
    Formula derived from Nielsen 2022 [DOI: 10.1109/LGRS.2022.3169994]

    Arguments
    ---------
    HHHH, HHHV, HVHV, HVVV, HHVV, VVVV : float
        The six components of UAVSAR GRD data.

    Returns
    -------
    C3 : np.array [3x3]
        C3 matrix with complex dtype.
    """
    # Lower triangular components
    c11 = HHHH
    c12 = np.sqrt(2)*HHHV
    c13 = HHVV
    c22 = 2*HVHV
    c23 = np.sqrt(2)*HVVV
    c33 = VVVV
    # Upper components are conjugates of lower components
    c21 = np.conjugate(c12)
    c31 = np.conjugate(c13)
    c32 = np.conjugate(c23)
    # Assemble C3 matrix
    C3 = np.array([[c11,c12,c13],
                   [c21,c22,c23],
                   [c31,c32,c33]])
    return C3


def C3_to_T3(C3):
    """
    Converts covariance matrix C3 to coherency matrix T3. Translation of the
    PolSARPro C3_to_T3 function which can be found here (in C):
    https://github.com/EO-College/polsarpro/blob/master/Soft/src/lib/util_convert.c
    
    Arguments
    ---------
    C3 : np.array [3x3]
        C3 matrix (use output from calc_C3 function)
    
    Returns
    -------
    T3 : np.array [3x3]
        T3 matrix with complex dtype.
    """
    # Lower traigular components
    t11 = 0.5*(C3[0,0]+2*C3[0,2].real + C3[2,2])
    t21 = 0.5*(C3[0,0]-C3[2,2]) + (-C3[0,2].imag)*1j
    t31 = ((C3[0,1].real + C3[1,2].real) + (C3[0,1].imag - C3[1,2].imag)*1j)/np.sqrt(2)
    t22 = 0.5*(C3[0,0] - 2 * C3[0,2].real + C3[2,2])
    t32 = ((C3[0,1].real - C3[1,2].real) + (C3[0,1].imag + C3[1,2].imag)*1j)/np.sqrt(2)
    t33 = C3[1,1]
    # Upper components are conjugates of lower components
    t12 = np.conjugate(t21)
    t13 = np.conjugate(t31)
    t23 = np.conjugate(t32)
    # Assemble T3 matrix
    T3 = np.array([[t11,t12,t13],
                   [t21,t22,t23],
                   [t31,t32,t33]])
    
    return T3


def T3_to_alpha1(T3):
    """
    Calculates alpha1 decomposition product from the coherency matrix T3. Uses
    the  eigenvector-eigenvalue identity method described by Nielsen 2022 
    [DOI: 10.1109/LGRS.2022.3169994]. This is a per-pixel calculation.

    Arguments
    ---------
    T3 : np.array [3x3]
        T3 matrix (use output from C3_to_T3 function)
    
    Returns
    -------
    alpha_1 : float
        Alpha 1 angle in degrees. 
    """
    # Calculate M1, the first minor 
    m1 = T3[1:,1:]
    t3_values = np.linalg.eigvalsh(T3)
    t3, t2, t1 = t3_values
    m1_values = np.linalg.eigvalsh(m1)
    m2, m1 = m1_values
    e11 = np.sqrt(((t1 - m1)*(t1 - m2))/((t1-t2)*(t1-t3)))
    alpha_1 = np.rad2deg(np.arccos(e11))
    return alpha_1

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