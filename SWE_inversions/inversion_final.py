import numpy as np

def insar_swe(delta_phase, inc_angle, permittivity = None, density = None,
              method = 'guneriussen2001', wavelength = 0.238403545):
    """
    Calculates change in snow depth from SAR phase change. Requires either 
    permittivity data or density data and selection of the method to estimate 
    permittivity from density.

    Parameters
    ----------
    delta_phase : NumPy array
        Phase change data, likely read in using rasterio.
    inc_angle : NumPy array or float
        Incidence angle data. If NumPy array, must be the same shape as the
        phase change array. If float, a constant incidence angle [radians]
        will be applied to the entire scene.
    permittivity : NumPy array or float
        Permittivity data. If a value is provided here, density is ignored.
        If NumPy array, must be the same shape as the phase change array. If
        float, a constant permittivity will be applied to the entire scene.
    density : NumPy array or float
        Snow density data. A value here will only be used if permittivity is not
        provided. If NumPy array, must be the same shape as the phase change
        array. If float, a constant density [kg m-3] will be applied to the
        entire scene.
    method : 'guneriussen2001' or 'webb2021'
        The method used to calculate permittivity from the density data. Only
        used if permittivity is not provided. See references Guneriussen et al.
        2001 [DOI: 10.1109/36.957273] and Webb et al. 2021 [10.3390/rs13224617]
    wavelength : float
        Radar wavelength [m]. Default value of 0.238403545 m is for UAVSAR L-band.

    Returns
    -------
    delta_z : NumPy array, change in snow depth
    """
    # Check for either permittivity or density
    if permittivity == None and density == None:
        raise ValueError('Please provide either permittivity or density data.')
    # Check to make sure all rasters are the same size
    for i in [inc_angle, permittivity, density]:
        if type(i) == np.ndarray:
            if i.shape != delta_phase.shape:
                raise ValueError('All raster datasets must be the same shape.')

    # Calculate permittivity with density if perm. is not directly provided
    if not permittivity:
        print(f'No permittivity data provided -- calculating permittivity from snow density using method {method}.')

        if method == 'guneriussen2001':
            # Need to convert to [g cm-3] as in original paper
            perm = 1 + 1.6 * (density/1000) + 1.8 * (density/1000)**3
        elif method == 'webb2021':
            # Good to use [kg m-3]
            perm = 1 + 0.0014 * density + 2e-7 * density**2
        else:
            raise ValueError("Please choose a density calulation method from 'guneriussen2001' or 'webb2021'.")

    else:
        perm = permittivity

    # Calculate snow depth change
    delta_z = (-delta_phase * wavelength) / (4 * np.pi * (np.cos(inc_angle) - np.sqrt(perm - np.sin(inc_angle)**2)))

    return delta_z
