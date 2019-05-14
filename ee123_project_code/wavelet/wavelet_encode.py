import pickle
import argparse
from util import *
from compress_tools import *

import subprocess
import json

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input', required=True, help='input file name')
    parser.add_argument('-o', '--output', required=True, help='output file name')
    parser.add_argument('-y', '--y_down', required=True, help='downsampling factor in luminance channel')
    parser.add_argument('-c', '--c_down', required=True, help='downsampling factor in chrominace channels')

    parser.add_argument('--delta_y_dc', type=float, default=16, help='initial quantization factor for DC')
    parser.add_argument('--step_y_dc', type=float, default=1, help='scaling factor of quantization factor for DC')
    parser.add_argument('--delta_c_dc', type=float, default=16, help='initial quantization factor for DC')
    parser.add_argument('--step_c_dc', type=float, default=1, help='scaling factor of quantization factor for DC')

    parser.add_argument('--delta_y_rs', type=float, default=16, help='initial quantization factor for residuals')
    parser.add_argument('--step_y_rs', type=float, default=1,
                        help='scaling factor of quantization factor for residuals')
    parser.add_argument('--delta_c_rs', type=float, default=16, help='initial quantization factor for residuals')
    parser.add_argument('--step_c_rs', type=float, default=1,
                        help='scaling factor of quantization factor for residuals')

    parser.add_argument('--tf_y_dc', type=float, default=3,
                        help='luminance threshold factor of quantization factor for DC')
    parser.add_argument('--tf_r_dc', type=float, default=3,
                        help='r chrominance threshold factor of quantization factor for DC')
    parser.add_argument('--tf_b_dc', type=float, default=3,
                        help='b chrominance threshold factor of quantization factor for DC')
    parser.add_argument('--tf_y_rs', type=float, default=3,
                        help='luminance threshold factor of quantization factor for residuals')
    parser.add_argument('--tf_r_rs', type=float, default=3,
                        help='r chrominance threshold factor of quantization factor for residuals')
    parser.add_argument('--tf_b_rs', type=float, default=3,
                        help='b chrominance threshold factor of quantization factor for residuals')

    parser.add_argument('--level', type=int, default=2,
                        help='levels for wavelet')



    parser.add_argument('--no_residual', action='store_true', help='compress without using residuals')
    parser.add_argument('--no_wavelet', action='store_true', help='not use wavelet for residuals')

    args = parser.parse_args()

    input_name = args.input
    output_name = args.output
    y_downscale = float(args.y_down)
    rb_downscale = float(args.c_down)

    # The code assumes the frame rate is always integer
    framerate = int(get_frame_rate(input_name))

    stack = imageStack_load(input_name)
    h, w, _ = stack[0].shape
    enc = lossy_encode(stack, y_downscale, rb_downscale, residual=not args.no_residual)

    ys, rs, bs = enc

    new_ys = []
    new_rs = []
    new_bs = []

    # delta = args.delta
    # delta_step = args.step
    infos = []

    level = args.level

    print_y = True
    print_r = False
    print_b = False

    print('-----Y-----')
    for i, y in enumerate(ys):
        print('max', np.max(y),np.min(y))
        if args.no_residual or i == 0:
            print('wavelet frames')
            dec_y, sizes = wavedec_arr(y, args.delta_y_dc, args.step_y_dc, level, args.tf_y_dc, print_max=print_y)
            prev_dim = len(dec_y)
            infos.append(sizes)
        else: # use residuals
            if not args.no_wavelet: # use wavelet for residuals
                print('wavelet residuals')
                dec_y, sizes = wavedec_arr(y, args.delta_y_rs, args.step_y_rs, level, args.tf_y_rs, print_max=print_y)
                infos.append(sizes)
            else: # quantize the residuals
                print('quantize residuals', args.delta_y_rs)
                dec_y = quantize(y, args.delta_y_rs, args.tf_y_rs).ravel()
                dec_y = np.pad(dec_y, (0, prev_dim - len(dec_y)), 'constant')

        new_ys.append(dec_y)
    print()

    print('-----R-----')
    for i, r in enumerate(rs):
        if print_r:
            print(np.max(r),np.min(r))
        if args.no_residual or i == 0:
            print('wavelet frames')
            dec_r, sizes = wavedec_arr(r, args.delta_c_dc, args.step_c_dc, level, args.tf_r_dc, print_max=print_r)
            prev_dim = len(dec_r)
            infos.append(sizes)
        else:
            if not args.no_wavelet:
                print('wavelet residuals')
                dec_r, sizes = wavedec_arr(r, args.delta_c_rs, args.step_c_rs, level, args.tf_r_rs, print_max=print_r)
                infos.append(sizes)
            else:
                print('quantize residuals', args.delta_c_rs)
                dec_r = quantize(r, args.delta_c_rs, args.tf_r_rs).ravel()
                dec_r = np.pad(dec_r, (0, prev_dim - len(dec_r)), 'constant')
        new_rs.append(dec_r)
    print()

    print('-----B-----')
    for i, b in enumerate(bs):
        if print_b:
            print(np.max(b),np.min(b))
        if args.no_residual or i == 0:
            print('wavelet frames')
            dec_b, sizes = wavedec_arr(b, args.delta_c_dc, args.step_c_dc, level, args.tf_b_dc, print_b)
            prev_dim = len(dec_b)
            infos.append(sizes)
        else:
            if not args.no_wavelet:
                print('wavelet residuals')
                dec_b, sizes = wavedec_arr(b, args.delta_c_rs, args.step_c_rs, level, args.tf_b_rs, print_b)
                infos.append(sizes)
            else:
                print('quantize residuals', args.delta_c_rs)
                dec_b = quantize(b, args.delta_c_rs, args.tf_b_rs).ravel()
                dec_b = np.pad(dec_b, (0, prev_dim - len(dec_b)), 'constant')
        new_bs.append(dec_b)
    print()

    new_ys = np.array(new_ys)
    new_rs = np.array(new_rs)
    new_bs = np.array(new_bs)

    cys = compress_array(new_ys)
    crs = compress_array(new_rs)
    cbs = compress_array(new_bs)

    print('first frame')
    print(len(compress_array(new_ys[0:1])))
    print(len(compress_array(new_rs[0:1])))
    print(len(compress_array(new_bs[0:1])))
    print('residuals')
    print(len(compress_array(new_ys[1:])))
    print(len(compress_array(new_rs[1:])))
    print(len(compress_array(new_bs[1:])))


    pickle.dump([framerate, (h, w), cys, crs, cbs], open(output_name, 'wb'))

    with open('test.txt', 'w') as f:
        f.write(json.dumps(infos))

    subprocess.run(['zip','test.zip','test.txt',output_name])

    print('video size %.1f KB;' % (os.path.getsize(output_name) / 1000))
    print('info size %.1f KB;' % (os.path.getsize('test.txt') / 1000))
    print('zip size %.1f KB;' % (os.path.getsize('test.zip') / 1000))
