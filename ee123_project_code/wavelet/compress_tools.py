import cv2
import lzma
import pywt
import numpy as np
import matplotlib.pyplot as plt
from numpy.fft import *
from PIL import Image
from io import BytesIO
import sys


def rgb2ycrcb(im):
    return cv2.cvtColor(im[...,::-1], cv2.COLOR_BGR2YCR_CB)

def ycrcb2rgb(im):
    return cv2.cvtColor(im, cv2.COLOR_YCR_CB2BGR)[...,::-1]

def crop_center(img, scale):
    y, x = img.shape
    cropx = int(x * scale)
    cropy = int(y * scale)
    startx = x//2 - (cropx//2)
    starty = y//2 - (cropy//2)    
    return img[starty:starty+cropy, startx:startx+cropx]

def pad_zero(img, shape):
    y, x = shape
    cy, cx = img.shape
    output = np.zeros(shape, dtype=np.complex_)
    sx = x//2 - (cx//2)
    sy = y//2 - (cy//2)
    output[sy:sy+cy, sx:sx+cx] = img
    return output

def fftdownsample(im, factor):
    fourier = fftshift(fft2(im))
    fourier = crop_center(fourier, factor)
    fourier = ifftshift(fourier)
    output = ifft2(fourier)
    h0, w0 = im.shape
    h1, w1 = output.shape
    return output.real * (h1*w1) / (h0*w0)

def fftupsample(im, sz):
    fourier = fftshift(fft2(im))
    fourier = pad_zero(fourier, sz)
    fourier = ifftshift(fourier)
    output = ifft2(fourier)
    h0, w0 = im.shape
    h1, w1 = sz
    return output.real * (h1*w1) / (h0*w0)

def lossy_encode(stack, y_downscale, rb_downscale, residual=True):
    h, w, _ = stack[0].shape
    ys, rs, bs = [], [], []
    py, pr, pb = 0., 0., 0.
    for im in stack:
        im = rgb2ycrcb(im).astype(np.float64)
        y = fftdownsample(im[...,0], y_downscale)
        r = fftdownsample(im[...,1], rb_downscale)
        b = fftdownsample(im[...,2], rb_downscale)
        if residual:
            ys.append(y - py)
            rs.append(r - pr)
            bs.append(b - pb)
            py, pr, pb = y, r, b
        else:
            ys.append(y)
            rs.append(r)
            bs.append(b)
    return np.array(ys), np.array(rs), np.array(bs)

def map2pixel(im):
    return (im - np.min(im)) * 255 / (np.max(im)-np.min(im))

def lossy_decode(stack, sz, residual=True):
    ims = []
    ys, rs, bs = stack
    py, pr, pb = 0., 0., 0.
    for y, r, b in zip(ys, rs, bs):
        y = fftupsample(y, sz)
        r = fftupsample(r, sz)
        b = fftupsample(b, sz)
        if residual:
            y, r, b = y+py, r+pr, b+pb
            py, pr, pb = y, r, b
        im = np.dstack([y, r, b])
        print(np.max(im),np.min(im))
        im = np.clip(im, 0, 255)
        im = ycrcb2rgb(im.astype(np.uint8))
        im = cv2.bilateralFilter(im, 13, 75, 75)
        ims.append(im)
    return ims

def compress_array(arr):

    f = BytesIO()
    np.save(f, arr)
    arr_bytes = f.getvalue()
    f.close()

    compressed = lzma.compress(arr_bytes)
    print('compression ratio:', len(arr_bytes) / len(compressed))
    return compressed

def decomp_array(b):
    decomp = lzma.decompress(b)
    f = BytesIO(decomp)
    arr_rec = np.load(f)
    f.close()
    return arr_rec

def next_power_of_2(x, quantize_scale=16):
    x = x / 16
    return 1 if x == 0 else 2**np.ceil(np.log2(x))

def wavedec_arr(img, delta, delta_step, level=None, threshold_factor=3, print_max=False):
    coeffs = pywt.wavedec2(img, 'db4', level=level)
    r, c = coeffs[0].shape
    sizes = []
    max_int = 128

    # approximation coefficient
    max_val = max(abs(coeffs[0].ravel()))
    # scale = int(next_power_of_2(max_val))
    # scale = max(int(delta),int(delta * np.ceil(max_val / (max_int * delta))))
    scale = int(delta)
    sizes.append([r, c, scale])
    if print_max:
        print('wavelet', max_val, scale)
    count = r * c
    delta = int(scale / delta_step)

    # rest of detail coefficients
    for i,coeff in enumerate(coeffs[1:]):
        size = []
        for cd in coeff:
            max_val = max(abs(cd.ravel()))
            # scale = min(int(delta),int(delta * np.ceil(max_val / (max_int * delta))))
            # scale = int(next_power_of_2(int(delta * np.ceil(max_val / (max_int * delta)))))
            scale = delta
            if print_max:
                print('wavelet',max_val, scale)
            r, c = cd.shape
            size.append([r, c, scale])
            count += r * c
        # delta = int(scale / delta_step)
        sizes.append(size)

    # approximation coefficient
    arr = np.zeros(count, dtype=np.int8)
    r, c = coeffs[0].shape
    idx = r * c
    s_idx = 0
    scale = sizes[s_idx][2]
    arr[:idx] = quantize(coeffs[0], scale, threshold_factor, print_max).ravel()
    assert np.max(abs(arr[:idx])) < 127, np.max(abs(arr[:idx]))


    # rest of detail coefficients
    for coeff in coeffs[1:]:
        s_idx += 1
        for i, cd in enumerate(coeff):
            r, c = cd.shape
            scale = sizes[s_idx][i][2]
            arr[idx:idx + r * c] = quantize(cd, scale, threshold_factor, print_max).ravel()
            idx += r * c

    return arr, sizes


def waverec_arr(arr, sizes, bias=0):
    coeffs = []
    size = sizes[0]
    length = size[0] * size[1]

    coeffs.append(dequantize(arr[:length], size[2], bias).reshape((size[0], size[1])))
    idx = length
    i = 0

    for size in sizes[1:]:
        coeff = []
        for s in size:
            length = s[0] * s[1]
            coeff.append(dequantize(arr[idx:idx + length], s[2], bias).reshape((s[0], s[1])))
            idx += length
        coeffs.append(coeff)

    return pywt.waverec2(coeffs, 'db4')


def quantize(coeff, scale, threshold=3, print_th=False):
    if print_th:
        print('threshold', threshold * scale)
    idx = np.where(np.abs(coeff) < threshold * scale)
    coeff[idx] = 0
    # new_coeff = np.sign(coeff) * ((np.abs(coeff) + 0.5 * scale) // scale)
    # return new_coeff.astype(np.int8)

    return (np.sign(coeff)*(abs(coeff) // scale)).astype(np.int8)

def dequantize(coeff, scale, bias=0.0):
    return np.sign(coeff) * (abs(coeff) + bias) * scale

# def quantize1(coeff, scale):
#     f_min = np.min(coeff)
#     new_coeff = np.floor((coeff - f_min) / scale)
#     return new_coeff.astype(np.int8)

#
# def dequantize1(coeff, f_min, scale=10, bias=0.0):
#     return coeff * scale  + scale/2 + f_min
#     # return np.sign(coeff) * scale/2 + f_min