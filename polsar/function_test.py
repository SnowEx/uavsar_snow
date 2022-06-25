from polsar_functions import H_A_alpha_decomp
from time import time

st = time()

in_dir = '/home/zacharykeskinen/Documents/uavsar_snow/polsar_imgs/uticam_21003_21004_002_210120_L090_CX_01_grd'
out_dir = '/home/zacharykeskinen/Documents/uavsar_snow/polsar_imgs/testing'
out = H_A_alpha_decomp(in_dir, out_dir, parralel =True)

et = time()
print(f'Time: {(et-st)/60} minutes')