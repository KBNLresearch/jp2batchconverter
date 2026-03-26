#! /usr/bin/env python3

"""JP2 Batch converter

Johan van der Knijff

Copyright 2026, KB/National Library of the Netherlands

"""

import sys
import os
import io
import shutil
import time
import argparse
import csv
import json
import logging
from lxml import etree
from . import shared
from .grok import Grok
from . import pixelcheck

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


def getConfiguration(configFile):
    """read configuration file and return contents as dictionary"""

    configDict = {}

    # Read config file to dictionary
    try:
        with io.open(configFile, 'r', encoding='utf-8') as f:
            configDict = json.load(f)
    except:
        raise

    return configDict


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


def processFiles(listFiles, dirIn, dirOut, configDict):
    """Process all files in list"""

    # Start Grok class instance
    grok = Grok()
    grok.configDict = configDict
    grok.configure()
    grok.compressionProfile = "KB_MASTER_LOSSLESS_01/01/2015"
    #grok.compressionProfile = "KB_ACCESS_LOSSY_01/01/2015"

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
        fileNameOut = "{}.{}".format(pre, "jp2")

        fileOut = os.path.abspath(os.path.join(filePathOut, fileNameOut))

        # Pass I/O to Grok instance and run the conversion
        grok.imageIn = fileIn
        grok.jp2Out = fileOut
        grok.compress()

        # Pixel check
        sumPixelDifferences = pixelcheck.sumDifferences(fileIn, fileOut)

        logging.info("Sum of absolute pixel differences: {}".format(sumPixelDifferences))


def main():
    """Main function"""

    # Path to configuration dir (from https://stackoverflow.com/a/53222876/1209004
    # and https://stackoverflow.com/a/13184486/1209004).
    configPath = os.path.join(
    os.environ.get('LOCALAPPDATA') or
    os.environ.get('XDG_CONFIG_HOME') or
    os.path.join(os.environ['HOME'], '.config'),
    "jp2batchconverter")

    # Locate package directory
    packageDir = os.path.dirname(os.path.abspath(__file__))

    # Config locations in installed package and system config folder
    configDirPackage = os.path.join(packageDir, "conf")

    # Check if package conf dir exists
    shared.checkDirExists(configDirPackage)

    # Copy config file from package to system config dir
    if not os.path.isdir(configPath):
        shutil.copytree(configDirPackage, configPath, dirs_exist_ok = True)

    configFile = os.path.join(configPath, "config.json")
    if not os.path.isfile(configFile):
        msg = "configuration file ({}) is missing".format(configFile)
        shared.errorExit(msg)

    # Read config file
    configDict = getConfiguration(configFile)

    # TODO validate contents of config file for completeness

    # List of file extensions to process (case insensitive)
    # TODO perhaps allow user to override this using command-line option?
    extensions = configDict["inExtensions"]

    # Get input from command line
    args = parseCommandLine()
    dirIn = os.path.normpath(args.dirIn)
    dirOut = os.path.normpath(args.dirOut)

    # Check if files / directories exist
    shared.checkDirExists(dirIn)
    if not os.path.isdir(dirOut):
        try:
            os.makedirs(dirOut)
        except exception:
            msg = "creation of output directory {} failed".format(outDir)
            shared.errorExit(msg)

    # Check if outDir is writable
    if not os.access(dirOut, os.W_OK):
        msg = "directory {} is not writable".format(outDir)
        shared.errorExit(msg)

    # Set up logging
    logFile = os.path.join(dirOut, 'jp2batchconverter.log')
    logging.basicConfig(handlers=[logging.StreamHandler(sys.stdout),
                                  logging.FileHandler(logFile, 'a', 'utf-8')],
                        level=logging.INFO,
                        format='%(asctime)s - %(levelname)s - %(message)s')

    # List of all files
    listFiles = getFilesFromTree(dirIn, extensions)

    # Start clock for statistics
    start = time.time()
    logging.info("jp2batchconverter started: {}".format(time.asctime()))

    # Process all files
    processFiles(listFiles, dirIn, dirOut, configDict)

    # Timing output
    end = time.time()
    logging.info("jp2batchconverter ended: {}".format(time.asctime()))
    # Elapsed time (seconds)
    timeElapsed = end - start
    timeInMinutes = round((timeElapsed / 60), 2)
    logging.info("Elapsed time: {} minutes".format(timeInMinutes))



if __name__ == "__main__":
    main()
