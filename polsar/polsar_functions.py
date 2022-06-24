"""
Overview slideshow of Polsar:
https://dges.carleton.ca/courses/IntroSAR/Winter2019/SECTION%203%20-%20Carleton%20SAR%20Training%20-%20SAR%20Polarimetry%20%20-%20Final.pdf

Relevant
Nielsen 2022: DOI 10.1109/LGRS.2022.3169994
Cloude and Pottier 1997 [DOI: 10.1109/36.551935]
"""

import math
import numpy as np
from glob import glob
from os.path import join, basename
from uavsar_pytools.convert.tiff_conversion import read_annotation


def get_polsar_stack(in_dir, bounds = False):
    """
    Reads UAVSAR GRD files from input directory.

    Arguments
    ---------
    in_dir : str
        Input directory that contains UAVSAR GRD data. Must have all 
        crosspruducts (HHHH, HVHV, VVVV, HHHV, HVHV, and HVVV) and the 
        associated .ann file.

    
    bounds (optional) : Subset to x_min, x_max, y_min, y_max in pixels.
    
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
        if bounds:
            xmin, xmax, ymin, ymax = bounds
            arr = arr[xmin:xmax,ymin:ymax]
        # arr = np.ma.masked_invalid(arr)
        pol[name] = arr
    
    stack = np.dstack([pol['HHHH'], pol['HHHV'], pol['HVHV'], pol['HVVV'], pol['HHVV'], pol['VVVV']])
    
    return stack


def calc_C3(HHHH, HHHV, HVHV, HVVV, HHVV, VVVV):
    """
    Calculates covariance matrix C3 from individual UAVSAR pixel locations. 
    Formula derived from Cloude and Pottier 1997 [DOI: 10.1109/36.551935]

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
    the eigenvector-eigenvalue identity method described by Nielsen 2022 
    [DOI: 10.1109/LGRS.2022.3169994]. This is a per-pixel calculation.

    Arguments
    ---------
    T3 : np.array [3x3]
        T3 matrix (use output from C3_to_T3 function)
    
    Returns
    -------
    alpha_1 : float
        alpha 1 angle in degrees. 
    """
    # Calculate M1, the first minor of T3 by deleting first row/col
    M1 = T3[1:,1:]
    # Calculate eigenvalues
    t3, t2, t1 = np.linalg.eigvalsh(T3)
    m2, m1 = np.linalg.eigvalsh(M1)
    # Eigenvector component from Nielsen 2022
    e11 = np.sqrt(((t1 - m1)*(t1 - m2))/((t1-t2)*(t1-t3)))
    alpha_1 = np.rad2deg(np.arccos(e11))
    
    return alpha_1

def T3_to_mean_alpha(T3):
    """
    Calculates mean alpha angle decomposition product from the coherency matrix 
    T3. Uses the eigenvector-eigenvalue identity method described by Nielsen 2022 
    [DOI: 10.1109/LGRS.2022.3169994]. This is a per-pixel calculation.

    Arguments
    ---------
    T3 : np.array [3x3]
        T3 matrix (use output from C3_to_T3 function)
    
    Returns
    -------
    mean_alpha : float
        mean alpha angle in degrees. 
    """
    M1 = T3[1:,1:]
    # Calculate eigenvalues
    t3, t2, t1 = np.linalg.eigvalsh(T3)
    m2, m1 = np.linalg.eigvalsh(M1)
    # Eigenvector components from Nielsen 2022
    e11 = np.sqrt(((t1 - m1)*(t1 - m2))/((t1-t2)*(t1-t3)))
    alpha_1 = np.arccos(e11)
    e21 = np.sqrt(((t2 - m1)*(t2-m2))/((t2-t1)*(t2-t3)))
    alpha_2 = np.arccos(e21)
    e31 = np.sqrt(((t3 - m1)*(t3-m2))/((t3-t1)*(t3-t2)))
    alpha_3 = np.arccos(e31)
    # Calculate weighted eigenvalues
    t3_values = [t3, t2, t1]
    weighted = t3_values/np.sum(t3_values)
    mean_alpha = weighted[2]*alpha_1 + weighted[1]*alpha_2 + weighted[0]*alpha_3
    mean_alpha = np.rad2deg(mean_alpha)
    
    return mean_alpha
    

def T3_to_H(T3):
    """
    Calculates entropy (H) decomposition product from the coherency matrix T3.
    Formula from Cloude and Pottier 1997 [DOI: 10.1109/36.551935]. This is a 
    per-pixel calculation.

    Arguments
    ---------
    T3 : np.array [3x3]
        T3 matrix (use output from C3_to_T3 function)
    
    Returns
    -------
    H : float
        Entropy (0 <= H <= 1).
    """
    values = np.linalg.eigvalsh(T3)
    weighted = values/np.sum(values)
    # Sum weighted values for H calculation
    h = 0
    for i in range(3):
        h +=  weighted[i] * math.log(weighted[i], 3)
    h *= -1
    return h


def T3_to_A(T3):
    """
    Calculates anisotropy (A) decomposition product from the coherency matrix 
    T3. Formula from Cloude and Pottier 1997 [DOI: 10.1109/36.551935]. This is 
    a per-pixel calculation.

    Arguments
    ---------
    T3 : np.array [3x3]
        T3 matrix (use output from C3_to_T3 function)
    
    Returns
    -------
    A : float
        Anisotropy (0 <= H <= 1).
    """
    values = np.linalg.eigvalsh(T3)
    A = (values[1] - values[0]) / (values[1] + values[0])
    return A


def decomp_components(stack, mean_alpha=True):
    """
    Function to calculate H-A-alpha (entropy-anisotropy-alpha) decomposition 
    from a stack of UAVSAR data. This function operates over the depth axis of 
    the stack and can be applied to an entire scene/array using 
    np.apply_along_axis. Can also calculate mean alpha using boolean keyword.

    Arguments
    ---------
    stack : np.array
        Array of size [n x m x 6] containing UAVSAR data. Can use the output of 
        the get_polsar_stack function. 
    mean_alpha : bool
        If True, calculates and returns mean alpha product in addition to H, A, 
        and alpha.

    Returns
    -------
    H, A, alpha1 (opt. meanalpha) : float
        Decomposition products calculated at a given pixel location.
    """
    if np.any(np.isnan(stack)):
        if mean_alpha:
            return np.repeat(np.nan, 4)
        else:
            return np.repeat(np.nan, 3)
    # Matrices
    C3 = calc_C3(*stack)
    T3 = C3_to_T3(C3)
    # Decomposition products
    H = T3_to_H(T3)
    A = T3_to_A(T3)
    alpha1 = T3_to_alpha1(T3)
    
    if mean_alpha:
        meanalpha = T3_to_mean_alpha(T3)
        return H, A, alpha1, meanalpha
    else:
        return H, A, alpha1
    

def uavsar_H_A_alpha(stack, mean_alpha=True):
    """
    Apply-along-axis version of decomp_products function. This function can be 
    used to perform H-A-alpha decomposition on a full UAVSAR scene. 
    """
    out = np.apply_along_axis(decomp_components, mean_alpha=mean_alpha, 
                              axis=2, arr=stack)

    H = out[:,:,0]
    A = out[:,:,1]
    alpha1 = out[:,:,2]
    if out.shape[-1] > 3:
        mean_alpha = out[:,:,3]
        return H, A, alpha1, mean_alpha
    else:
        return H, A, alpha1
