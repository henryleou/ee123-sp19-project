import os
import pickle
import argparse
from util import *
from compress_tools import *
import json
import scipy.signal
import scipy.ndimage
import numpy as np


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input', required=True, default='test.zip', help='input file name')
    parser.add_argument('-o', '--output', required=True,  help='output path')
    parser.add_argument('-r', '--ref', help='reference image')

    parser.add_argument('--delta_y_rs', type=float, default=16, help='initial quantization factor for residuals')
    parser.add_argument('--delta_c_rs', type=float, default=16, help='initial quantization factor for residuals')

    parser.add_argument('--no_residual', action='store_true', help='compress without using residuals')
    parser.add_argument('--no_wavelet', action='store_true', help='not use wavelet for residuals')

    args = parser.parse_args()
    
    input_name = args.input
    output_path = args.output

    subprocess.run(['unzip', '-o', input_name, '-d', 'test_decode'])

    framerate, sz, cys, crs, cbs = pickle.load(open(os.path.join('test_decode','test.p'), 'rb'))

    dys = decomp_array(cys).astype(np.float64)
    drs = decomp_array(crs).astype(np.float64)
    dbs = decomp_array(cbs).astype(np.float64)
    # else:
    #     framerate, sz, cyf, cyr, ryf, ryr, byf, byr = pickle.load(open(os.path.join('test_decode', 'test.p'), 'rb'))
    #
    #     dyf = decomp_array(cyf).astype(np.float64)
    #     dyr = decomp_array(cyr).astype(np.float64)
    #     dys = np.vstack((dyf,dyr))
    #
    #     drf = decomp_array(ryf).astype(np.float64)
    #     drr = decomp_array(ryr).astype(np.float64)
    #     drs = np.vstack((drf,drr))
    #
    #     dbf = decomp_array(byf).astype(np.float64)
    #     dbr = decomp_array(byr).astype(np.float64)
    #     dbs = np.vstack((dbf,dbr))


    new_ys = []
    new_rs = []
    new_bs = []

    infos = json.load(open(os.path.join('test_decode','test.txt')))

    bias = 0.0
    quantized = args.no_wavelet and not args.no_residual # residual is used with no wavelet
    for i,y in enumerate(dys):
        if not quantized or i == 0:
            sizes = infos.pop(0)
            rec_y = waverec_arr(y,sizes,bias)
            h,w = rec_y.shape
        else:
            rec_y = dequantize(y[:h*w],args.delta_y_rs).reshape((h,w))
        new_ys.append(rec_y)

    print()
    for i,r in enumerate(drs):
        if not quantized or i == 0:
            sizes = infos.pop(0)
            rec_r = waverec_arr(r,sizes,bias)
            h,w = rec_r.shape
        else:
            rec_r = dequantize(r[:h*w],args.delta_c_rs).reshape((h,w))
        # print(rec_r[:10,:10])
        new_rs.append(rec_r)

    print()
    for i,b in enumerate(dbs):
        if not quantized or i == 0:
            sizes = infos.pop(0)
            rec_b = waverec_arr(b,sizes,bias)
            h,w = rec_b.shape
            print('wavelet reconstruction')
        else:
            print('quantize reconstruction')
            rec_b = dequantize(b[:h*w],args.delta_c_rs).reshape((h,w))
       # print(rec_b[:10,:10])
        new_bs.append(rec_b)

    new_ys = np.array(new_ys)
    new_rs = np.array(new_rs)
    new_bs = np.array(new_bs)

    ims = np.array(lossy_decode([new_ys, new_rs, new_bs], sz, not args.no_residual))
    print(ims.shape)

    # disk = np.array([[0, 0.0003, 0.0110, 0.0172, 0.0110, 0.0003, 0],
    #                  [0.0003, 0.0245, 0.0354, 0.0354, 0.0354, 0.0245, 0.0003],
    #                  [0.0110, 0.0354, 0.0354, 0.0354, 0.0354, 0.0354, 0.0110],
    #                  [0.0172, 0.0354, 0.0354, 0.0354, 0.0354, 0.0354, 0.0172],
    #                  [0.0110, 0.0354, 0.0354, 0.0354, 0.0354, 0.0354, 0.0110],
    #                  [0.0003, 0.0245, 0.0354, 0.0354, 0.0354, 0.0245, 0.0003],
    #                  [0, 0.0003, 0.0110, 0.0172, 0.0110, 0.0003, 0]])
    #
    # iterations = 30
    # new_ims = ims.copy().astype(np.float64)
    # for i in range(ims.shape[0]):
    #     for j in range(3):
    #         f_img = scipy.signal.wiener(ims[i,:,:,j].copy().astype(np.float64),mysize=3)
    #         b_wiener = f_img.copy()
    #         for i in range(iterations + 1):
    #             conv = scipy.ndimage.filters.correlate(f_img, disk)
    #             f_img = f_img + 0.1 * (b_wiener - conv)
    #             f_img = f_img.clip(min=0)
    #             f_img = f_img.clip(max=255)
    #         print(new_ims[0].shape)
    #         # print(f_img.shape)
    #         # print(new_ims[i,:,:,j].shape)
    #         new_ims[i,:,:,j] = f_img
    # new_ims = new_ims.astype(np.uint8)

    imageStack_save(ims, output_path, framerate)

    ref_img = np.array(imageStack_load(args.ref))

    # print(psnr(ims[0]/1.0,ref_img[0]/1.0))
    # print(psnr( ((ims[1:]/1.0-ims[0:-1]/1.0)),((ref_img[1:]/1.0-ref_img[0:-1]/1.0))))

    print('psnr:', psnr(np.array(ims), ref_img))
    # print()
    # for i in range(len(ref_img)):
    #     print(psnr(ims[i],ref_img[i]))


