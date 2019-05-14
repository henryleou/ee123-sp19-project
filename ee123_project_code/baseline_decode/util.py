import numpy as np

from PIL import Image
import time
import glob
import os
import sys
import subprocess
# import bokeh.plotting as bk
# from bokeh.io import push_notebook
# from bokeh.resources import INLINE
# from bokeh.models import GlyphRenderer

# bk.output_notebook(INLINE)

import re

numbers = re.compile(r'(\d+)')

def numericalSort(value):
    parts = numbers.split(value)
    parts[1::2] = map(int, parts[1::2])
    return parts


# # Tiff stack player

# def Tiff_play(path, display_size, frame_rate):
#     image_files = sorted(glob.glob(path), key=numericalSort)
#     Nframe = len(image_files)

#     im = Image.open(image_files[0])
#     xdim, ydim= im.size
#     display_array = np.zeros((Nframe,ydim,xdim,4),dtype='uint8')
    
#     # load image stack
#     for i in range(0,Nframe):
#         im = Image.open(image_files[i])
#         im = im.convert("RGBA")
#         imarray = np.array(im)
#         display_array[i] = np.flipud(imarray)
        
#     # Play video

#     wait_time = 1/frame_rate
#     normalized_size = display_size
#     max_size = np.maximum(xdim,ydim)
#     width = (xdim/max_size * normalized_size).astype('int')
#     height = (ydim/max_size * normalized_size).astype('int')
    
#     counter = 0
#     first_round = True
#     try:
#         while True:
#             if counter == 0 and first_round:
#                 p = bk.figure(x_range=(0,xdim), y_range=(0,ydim), plot_height = height, plot_width = width)
#                 p.image_rgba(image=[display_array[counter]], x=0, y=0, dw=xdim, dh=ydim, name='video')
#                 bk.show(p, notebook_handle=True)
#                 counter += 1
#                 first_round = False
#             else:
#                 renderer = p.select(dict(name='video', type=GlyphRenderer))
#                 source = renderer[0].data_source
#                 source.data['image'] = [display_array[counter]]
#                 push_notebook()
#                 if counter == Nframe-1:
#                     counter = 0
#                 else:
#                     counter += 1
#             time.sleep(wait_time)
            
#     except KeyboardInterrupt:
#         pass
            
# Image_stack loader

def Tiff_load(path):
    image_files = sorted(glob.glob(path), key=numericalSort)
    Nframe = len(image_files)
    
    im = Image.open(image_files[0])
    xdim, ydim= im.size
    image_stack = np.zeros((Nframe,ydim,xdim,3),dtype='uint8')
    
    for i in range(0,Nframe):
        im = Image.open(image_files[i])
        image_stack[i] = np.array(im)
    
    return image_stack

# Image_stack loader with ffmpeg

def imageStack_load(filename):
    path        = filename[:filename.find('.')]+'/'
    os.system("rm -rf {:s}".format(path))
    os.system("mkdir {:s}".format(path))
    os.system("ffmpeg -i {:s} {:s}frame_%2d.tiff".format(filename, path))
    image_files = sorted(glob.glob(path+"*.tiff"), key=numericalSort)
    Nframe = len(image_files)
    
    im = Image.open(image_files[0])
    xdim, ydim= im.size
    image_stack = np.zeros((Nframe,ydim,xdim,3),dtype='uint8')
    
    for i in range(0,Nframe):
        im = Image.open(image_files[i])
        image_stack[i] = np.array(im)
    
    return image_stack

# Save image stack

def imageStack_save(stack, path, framerate):
    os.system("rm -rf {:s}".format(path))
    os.system("mkdir {:s}".format(path))
    for i in range(len(stack)):
        Image.fromarray(stack[i]).save('%s/frame_%02d.tiff' % (path, i))
    GIF_save(path, framerate)

# Save gif with ffmpeg

def GIF_save(path, framerate):
    os.system("ffmpeg -r {:d} -i {:s}/frame_%2d.tiff -compression_level 0 -plays 0 -f apng {:s}/animation.png".format(framerate, path,path))

# Get framerate of the video

def get_frame_rate(filename):
    if not os.path.exists(filename):
        sys.stderr.write("ERROR: filename %r was not found!" % (filename,))
        return -1         
    out = subprocess.check_output(["ffprobe",filename,"-v","0","-select_streams","v","-print_format","flat","-show_entries","stream=r_frame_rate"])
    rate = str(out).split('=')[1].split('"')[1].split('/')
    if len(rate) == 1:
        return float(rate[0])
    if len(rate) == 2:
        return float(rate[0]) / float(rate[1])
    return -1

# Compute video PSNR

def psnr(ref, meas, maxVal=255):
    assert np.shape(ref) == np.shape(meas), "Test video must match measured vidoe dimensions"


    dif = (ref.astype(float)-meas.astype(float)).ravel()
    mse = np.linalg.norm(dif)**2/np.prod(np.shape(ref))
    psnr = 10*np.log10(maxVal**2.0/mse)
    return psnr

