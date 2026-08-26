#! /usr/bin/env python3

import os

extensionsIn = ["TIFF", "TIF"]
#dirIn = "/home/johan/kb/digitalisering/tifftojp2/mh-small-tiff"
dirIn = "/media/johan/Seba_MH/batchesTIFF/MMHKB01_000000047_3_01"
noFiles = 0

# Iterate over directories and files in batch
for dirname, dirnames, filenames in os.walk(dirIn):
    for filename in filenames:
            thisExtension = os.path.splitext(filename)[1]
            thisExtension = thisExtension.upper().strip('.')
            if thisExtension in extensionsIn:
                noFiles += 1

print(noFiles)
