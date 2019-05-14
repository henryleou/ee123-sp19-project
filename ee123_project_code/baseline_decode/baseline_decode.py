import os
import pickle
import argparse
from util import *
from compress_tools import *
# from wavelet_tools import *


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input', required=True, help='input file name')
    parser.add_argument('-o', '--output', required=True, help='output path')
    parser.add_argument('--y_scale', required=True, help='quantize factor in luminance channel')
    parser.add_argument('--c_scale', required=True, help='quantize factor in chrominace channels')
    parser.add_argument('--no_residual', action='store_true', help='without residuals')
    parser.add_argument('--ref', required=True, help='reference video for psnr')
    args = parser.parse_args()
    
    input_name = args.input
    output_path = args.output
    y_scale = int(args.y_scale)
    c_scale = int(args.c_scale)
    framerate, sz, cys, crs, cbs = pickle.load(open(input_name, 'rb'))
    
    dys = decomp_array(cys).astype(np.float64)
    drs = decomp_array(crs).astype(np.float64)
    dbs = decomp_array(cbs).astype(np.float64)
    
    dys = dequantize(dys, scale=y_scale)
    drs = dequantize(drs, scale=c_scale)
    dbs = dequantize(dbs, scale=c_scale)

    ims = lossy_decode([dys, drs, dbs], sz, residual=not args.no_residual)
    imageStack_save(ims, output_path, framerate)
    
    ref_img = np.array(imageStack_load(args.ref))
    print('psnr:', psnr(np.array(ims), ref_img))
    print()
    for i in range(len(ref_img)):
        print(psnr(ims[i],ref_img[i]))
