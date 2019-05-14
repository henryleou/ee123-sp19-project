import pickle
import argparse
from util import *
from compress_tools import *
# from wavelet_tools import *


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input', required=True, help='input file name')
    parser.add_argument('-o', '--output', required=True, help='output file name')
    parser.add_argument('-y', '--y_down', required=True, help='downsampling factor in luminance channel')
    parser.add_argument('-c', '--c_down', required=True, help='downsampling factor in chrominace channels')
    parser.add_argument('--y_scale', required=True, help='quantize factor in luminance channel')
    parser.add_argument('--c_scale', required=True, help='quantize factor in chrominace channels')
    parser.add_argument('--no_residual', action='store_true', help='without residuals')

    parser.add_argument('--tf_dc', type=float, default=3,
                        help='threshold factor of quantization factor for DC')
    parser.add_argument('--tf_rs', type=float, default=3,
                        help='threshold factor of quantization factor for residuals')

    args = parser.parse_args()
    
    input_name = args.input
    output_name = args.output
    y_downscale = float(args.y_down)
    rb_downscale = float(args.c_down)
    y_scale = int(args.y_scale)
    c_scale = int(args.c_scale)
    
    # The code assumes the frame rate is always integer
    framerate = int(get_frame_rate(input_name))
    
    stack = imageStack_load(input_name)
    h, w, _ = stack[0].shape
    enc = lossy_encode(stack, y_downscale, rb_downscale, residual=not args.no_residual)
    
    ys, rs, bs = enc
    qys = quantize(ys, scale=y_scale)
    qrs = quantize(rs, scale=c_scale)
    qbs = quantize(bs, scale=c_scale)

    cys = compress_array(qys)
    crs = compress_array(qrs)
    cbs = compress_array(qbs)
    
    pickle.dump([framerate, (h, w), cys, crs, cbs], open(output_name, 'wb'))
    print('compressed size %.1f KB:' % (os.path.getsize(output_name) / 1000))
