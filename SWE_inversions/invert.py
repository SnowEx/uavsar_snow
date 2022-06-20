import numpy as np

def epsilon_density(p):
    # From Guneriussen et al. (2001) - Eq. 7
    return 1 + 1.6*p + 1.8 * p**3

def invert_sd(unw, inc, wavelength = 0.238403545, epsilon = 1.42):
    # From Marshall et al. (2021) Eq 1 which drew on Guneriussen et al. (2001)
    sd = - (unw * wavelength)/ (4 * np.pi) / (np.cos(inc) - np.sqrt(epsilon - (np.sin(inc)**2)))
    return sd