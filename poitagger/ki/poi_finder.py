# takes in a patch and findes where the kitz is 
import numpy as np
import cv2 as cv
from . import files
from . import patchmaker

upscale = 16
patchsize = 64


gauss_rad = 3

def make_bw(patch):
    thresh = 255 - (np.mean(patch) * 2)
    bw = cv.threshold(patch, thresh, 255, cv.THRESH_BINARY)[1]
    return bw


def find_brightest(patch, to_file=False):
    # apply a Gaussian blur to the image then find the brightest
    # region
    patchn = patch['patch_array']
    #print(patch)
    x0,y0 = patchmaker.get_patch_uleft(patch["patchnr"])
    gray = cv.cvtColor(patchn, cv.COLOR_BGR2GRAY)
    # blurred = cv.GaussianBlur(gray, (gauss_rad, gauss_rad), 0)
    (minVal, maxVal, minLoc, maxLoc) = cv.minMaxLoc(gray)
    if to_file:
        files.write_brightest_patch(patch, upscale, patchsize ,maxLoc, gauss_rad)
    maxLocAbs = (x0 + maxLoc[0], y0 + maxLoc[1])
    
    return maxLoc, maxVal,maxLocAbs

def is_poi_test(haskitz, confidence, img_meta, conf_thresh):
    if (haskitz and confidence >= conf_thresh and
        img_meta["uav_lon"] is not None and
        img_meta["uav_lat"] is not None):
            return True
    else:
        return False

def is_poi(haskitz, confidence, img_meta, conf_thresh):
    if (haskitz and confidence >= conf_thresh and
        img_meta["uav_lon"] is not None and
        img_meta["uav_lat"] is not None and
        -100 <= img_meta['cam_pitch'] <= -80 and
        -10 <= img_meta['cam_roll'] <= 10 and
        img_meta['uav_ele'] >= 35):
            return True
    else:
        return False