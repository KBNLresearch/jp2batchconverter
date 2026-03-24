#! /usr/bin/env python3

"""JP2 Batch converter

Johan van der Knijff

Copyright 2026, KB/National Library of the Netherlands

"""

import sys
import os
import shutil
import time
import argparse
import csv
import logging
from lxml import etree
from . import shared
from . import kakadu

__version__ = "0.1.0"

# Create parser
parser = argparse.ArgumentParser(description="JP2 Batch converter")


def parseCommandLine():
    """Parse command line"""
    # Add arguments
    parser.add_argument('dirIn',
                        action="store",
                        type=str,
                        help="input directory")
    parser.add_argument('dirOut',
                        action="store",
                        type=str,
                        help="output directory")
    parser.add_argument('--version', '-v',
                        action='version',
                        version=__version__)


    # Parse arguments
    args = parser.parse_args()

    return args


def getFilesFromTree(rootDir, extensions):
    """Walk down whole directory tree (including all subdirectories) and
    return list of files whose extensions match extensions list
    NOTE: directory names are disabled here!!
    implementation is case insensitive (all search items converted to
    upper case internally!
    """

    # Convert extensions to uppercase
    extensions = [extension.upper() for extension in extensions]
    filesList = []

    for dirname, dirnames, filenames in os.walk(rootDir):
        # Suppress directory names
        for subdirname in dirnames:
            thisDirectory = os.path.join(dirname, subdirname)

        for filename in filenames:
            if filename.startswith("._"):
                # Ignore AppleDouble resource fork files (identified here by name)
                pass
            else:
                thisFile = os.path.join(dirname, filename)
                thisExtension = os.path.splitext(thisFile)[1]
                thisExtension = thisExtension.upper().strip('.')
                if extensions[0].strip() == '*' or thisExtension in extensions:
                    filesList.append(thisFile)
    return filesList


def processFiles(listFiles, dirIn, dirOut):
    """Process all files in list"""

    for fileIn in listFiles:
        logging.info(("file: {}").format(fileIn))
        fileNameIn = os.path.basename(fileIn)
        filePathIn = os.path.dirname(fileIn)
        filePathInRel = os.path.relpath(filePathIn, start=dirIn)
        filePathOut = os.path.abspath(os.path.join(dirOut, filePathInRel))

        # Create filePathOut if it doesn't exist (including any missing parent dirs)
        if not os.path.isdir(filePathOut):
            os.makedirs(filePathOut)

        # Construct name for output file
        pre, ext = os.path.splitext(fileNameIn)
        fileNameOut = ("{}.{}".format(pre, "jp2"))

        fileOut = os.path.abspath(os.path.join(filePathOut, fileNameOut))

        ## TEST
        #print(fileIn)
        #print(fileOut)
        ## TEST
        kduDict = kakadu.compress(fileIn, fileOut)


def main():
    """Main function"""

    extensions = ["tiff", "tif"]

    # Path to configuration dir (from https://stackoverflow.com/a/53222876/1209004
    # and https://stackoverflow.com/a/13184486/1209004).
    # TODO on Windows this should return the AppData/Local folder, does this work??
    configpath = os.path.join(
    os.environ.get('LOCALAPPDATA') or
    os.environ.get('XDG_CONFIG_HOME') or
    os.path.join(os.environ['HOME'], '.config'),
    "jp2batchconverter")

     # Create config directory if it doesn't exist already
    if not os.path.isdir(configpath):
        os.mkdir(configpath)
   
    # Locate package directory
    packageDir = os.path.dirname(os.path.abspath(__file__))

    """
    TODO - replace code below with any configuration stuff that is specific to the JP2 batch converter
    # Profile and schema locations in installed package and config folder
    profilesDirPackage = os.path.join(packageDir, "profiles")
    schemasDirPackage = os.path.join(packageDir, "schemas")
    profilesDir = os.path.join(configpath, "profiles")
    schemasDir = os.path.join(configpath, "schemas")

    # Check if package profiles and schemas dirs exist
    shared.checkDirExists(profilesDirPackage)
    shared.checkDirExists(schemasDirPackage)

    # Copy profiles and schemas to respective dirs in config dir
    if not os.path.isdir(profilesDir):
        shutil.copytree(profilesDirPackage, profilesDir)
    if not os.path.isdir(schemasDir):
        shutil.copytree(schemasDirPackage, schemasDir)
    """

    # Get input from command line
    args = parseCommandLine()
    dirIn = os.path.normpath(args.dirIn)
    dirOut = os.path.normpath(args.dirOut)

    # Check if files / directories exist
    shared.checkDirExists(dirIn)
    shared.checkDirExists(dirOut)

    # Check if outDir is writable
    if not os.access(dirOut, os.W_OK):
        msg = ("directory {} is not writable".format(outDir))
        shared.errorExit(msg)

    # Set up logging
    logging.basicConfig(handlers=[logging.StreamHandler(sys.stdout)],
                        level=logging.INFO,
                        format='%(asctime)s - %(levelname)s - %(message)s')

    # List of all files
    listFiles = getFilesFromTree(dirIn, extensions)

    # Start clock for statistics
    start = time.time()
    print("jp2batchconverter started: " + time.asctime())

    # Process all files
    processFiles(listFiles, dirIn, dirOut)

    # Timing output
    end = time.time()

    print("jp2batchconverter ended: " + time.asctime())

    # Elapsed time (seconds)
    timeElapsed = end - start
    timeInMinutes = round((timeElapsed / 60), 2)

    print("Elapsed time: {} minutes".format(timeInMinutes))



if __name__ == "__main__":
    main()
