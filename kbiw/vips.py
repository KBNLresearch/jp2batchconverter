#! /usr/bin/env python3
"""Vips module"""

import os
import sys


class Vips:
    """Vips class"""

    def __init__(self, vipsBinDir):
        """Initialise Vips class instance
        on Windows we need to make sure vipsBinDir is available to pyvips"""
        if sys.platform == "win32":
            vipsBinDir = os.path.normpath(vipsBinDir)
            os.environ['PATH'] = os.pathsep.join((vipsBinDir, os.environ['PATH']))
        import pyvips
        self.pyvips = pyvips

    def sumSqDiff(self, image1, image2):
        """ Returns sum of squared difference between two images"""

        try:
            im1 = self.pyvips.Image.new_from_file(image1, access="sequential")
            im2 = self.pyvips.Image.new_from_file(image2, access="sequential")

            # Compute stats from differences image and convert to nested list
            stats = (im1 - im2).stats().tolist()
            # First child list contains aggregated statistics for all bands,
            # subsequent child lists contain statistics for individual bands.
            # Documented here:
            #
            # https://www.libvips.org/API/8.17/method.Image.stats.html
            #
            # Statistics for each list, in order:
            # minimum, maximum, sum, sum of squares, mean, standard deviation,
            # x coordinate of minimum, y coordinate of minimum,
            # xcoordinate of maximum, y coordinate of maximum.
            #
            # Return sum of squared differences (aggregated for all bands)
            ssDiff = stats[0][3]
        except Exception:
            ssDiff = None

        return ssDiff

    def convertPaletted(self, imageIn, imageOut):
        # Re-saves input image, which results in non-paletted output image
        try:
            im1 = self.pyvips.Image.new_from_file(imageIn, access="sequential")
            im1.write_to_file(imageOut)
            success = True
        except Exception:
            success = False

        return success
