#! /usr/bin/env python3

"""Compare pixel values from pair of images
"""

from PIL import Image
from PIL import ImageChops
from PIL import ImageStat

def sumDifferences(image1, image2):
    """ Returns sum of absolute differences between pixel values in pair of images"""
    success = True

    try:
        im1 = Image.open(image1)
        im2 = Image.open(image2)
        imDiff = ImageChops.difference(im1, im2)
        im1.close
        im2.close
        stat = ImageStat.Stat(imDiff)
        imDiff.close
        # This returns a list with separate values for each channel
        sumDiff = stat.sum
        # Sum all values so we have one number for all channels
        sumDiffAll = 0
        for value in sumDiff:
            sumDiffAll += value
    except Exception:
        sumDiffAll = None
        success = False

    return sumDiffAll, success
