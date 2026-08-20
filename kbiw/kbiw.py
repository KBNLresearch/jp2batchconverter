#! /usr/bin/env python3

"""KB Image Workflow Tool

Johan van der Knijff

Copyright 2026, KB/National Library of the Netherlands

"""

import sys
import os
import io
import shutil
import time
import argparse
import json
import logging
from . import shared
from .workflows import tifftojp2_generic
from .workflows import tifftojp2_mh

__version__ = "0.1.2"

# Create parser
parser = argparse.ArgumentParser(description="KB Image Workflow tool")


def parseCommandLine():
    """Parse command line"""
    # Add arguments
    parser.add_argument("dirIn",
                        action="store",
                        type=str,
                        help="input batch directory")
    parser.add_argument("dirOut",
                        action="store",
                        type=str,
                        help="output batch directory")
    parser.add_argument("workflow",
                        action="store",
                        type=str,
                        help="workflow (tifftojp2-generic, tifftojp2-generic-convertpaletted, tifftojp2-mh, tifftojp2-ie)")
    parser.add_argument("--version", "-v",
                        action="version",
                        version=__version__)

    # Parse arguments
    args = parser.parse_args()

    return args


def configure(configPath):
    """
    Set up configuration dir if it doesn't exist already, and read configuration
    """

    # Locate package directory
    packageDir = os.path.dirname(os.path.abspath(__file__))

    # Config locations in installed package and system config folder
    configDirPackage = os.path.join(packageDir, "conf")

    # Check if package conf dir exists
    shared.checkDirExists(configDirPackage)

    # Copy contents of package config dir to system config dir
    if not os.path.isdir(configPath):
        shutil.copytree(configDirPackage, configPath, dirs_exist_ok=True)

    configFile = os.path.join(configPath, "config.json")
    if not os.path.isfile(configFile):
        msg = "configuration file ({}) is missing".format(configFile)
        shared.errorExit(msg)

    cprofilesFile = os.path.join(configPath, "cprofiles.json")
    if not os.path.isfile(cprofilesFile):
        msg = "compression profiles file ({}) is missing".format(cprofilesFile)
        shared.errorExit(msg)

    # Read config and compression profiles to dictionaries
    configDict = {}
    cprofilesDict = {}

    try:
        with open(configFile, 'r', encoding='utf-8') as f:
            configDict = json.load(f)
    except:
        raise

    # Some light validation of config file contents
    if not "grokDir" in configDict:
        msg = "\"grokDir\" entry missing in configuration file"
        shared.errorExit(msg)
    if not "exifToolExecutable" in configDict:
        msg = "\"exifToolExecutable\" entry missing in configuration file"
        shared.errorExit(msg)
    if not "vipsBinDir" in configDict:
        msg = "\"vipsBinDir\" entry missing configuration file"
        shared.errorExit(msg)

    try:
        with open(cprofilesFile, 'r', encoding='utf-8') as f:
            cprofilesDict = json.load(f)
    except:
        raise

    if not "compressionProfiles" in cprofilesDict:
        msg = "\"compressionProfiles\" entry missing in compression profiles file"
        shared.errorExit(msg)

    for compressionProfile in cprofilesDict["compressionProfiles"]:
        if not "name" in compressionProfile:
            msg = "\"name\" entry missing in compression profiles file"
            shared.errorExit(msg)
        if type(compressionProfile["name"]) != str:
            msg = "\"name\" value is not a string"
            shared.errorExit(msg)
        if not "params" in compressionProfile:
            msg = "\"params\" entry missing in compression profiles file"
            shared.errorExit(msg)
        if type(compressionProfile["params"]) != list:
            msg = "\"params\" value is not a list"
            shared.errorExit(msg)

    return configDict, cprofilesDict


def main():
    """Main function"""

    # Path to configuration dir (from https://stackoverflow.com/a/53222876/1209004
    # and https://stackoverflow.com/a/13184486/1209004).
    configPath = os.path.join(
        os.environ.get('LOCALAPPDATA') or
        os.environ.get('XDG_CONFIG_HOME') or
        os.path.join(os.environ['HOME'], '.config'),
        "kbiw")

    # Get configuration, and set up local configuration if it doesn't exist
    configDict, cprofilesDict = configure(configPath)

    # Get input from command line
    args = parseCommandLine()
    dirIn = os.path.normpath(args.dirIn)
    dirOut = os.path.normpath(args.dirOut)
    workflow = os.path.normpath(args.workflow)

    # Check if files / directories exist
    shared.checkDirExists(dirIn)

    # Check if ExifTool executable exists and is executable
    exifToolExecutable = configDict["exifToolExecutable"]
    if not os.path.isfile(exifToolExecutable):
        msg = "exifToolExecutable ({}) not found".format(exifToolExecutable)
        shared.errorExit(msg)
    if not os.access(exifToolExecutable, os.X_OK):
        msg = "exifToolExecutable ({}) is not executable".format(
            exifToolExecutable)
        shared.errorExit(msg)

    # Check if vipsBinDir exists (Windows only)
    if sys.platform == "win32":
        vipsBinDir = configDict["vipsBinDir"]
        if not os.path.isdir (os.path.normpath(vipsBinDir)):
            msg = "vipsBinDir ({}) not found".format(vipsBinDir)
            shared.errorExit(msg)

    # Check if workflow value is valid
    workflowsAllowed = ["tifftojp2-mh", "tifftojp2-ie", "tifftojp2-generic"]
    if workflow not in workflowsAllowed:
        msg = "workflow \"{}\" does not exist. Expected one of these values:".format(
            workflow)
        for wf in workflowsAllowed:
            msg += "\n  - {}".format(wf)
        shared.errorExit(msg)

    # Create dirOut if it doesn't exist already
    if not os.path.isdir(dirOut):
        try:
            os.makedirs(dirOut)
        except exception:
            msg = "creation of output directory {} failed".format(outDir)
            shared.errorExit(msg)

    # Log file
    logFile = os.path.join(dirOut, 'kbiw.log')

    # Remove any previous log file instances
    if os.path.isfile(logFile):
        os.remove(logFile)

    # Set up logging
    logging.basicConfig(handlers=[logging.StreamHandler(sys.stdout),
                                  logging.FileHandler(logFile, 'a', 'utf-8')],
                        level=logging.INFO,
                        format='%(asctime)s - %(levelname)s - %(message)s')

    # Start clock for statistics
    start = time.time()
    logging.info("kbiw started: {}".format(time.asctime()))
    logging.info("starting workflow \"{}\"".format(workflow))

    # Run selected workflow
    if workflow == "tifftojp2-mh":
        # Middeleeuwse Handschriften
        wf = tifftojp2_mh.Workflow()
    elif workflow == "tifftojp2-ie":
        # Indisch Erfgoed
        wf = tifftojp2_generic.Workflow()
        # Compression profile
        wf.compressionProfile = "KB_MASTER_LOSSLESS_10/06/2026"
        # Schematron schema used for properties check
        wf.schema = "kbMaster_2026.sch"
        # List with names of directories that must be copied unchanged
        wf.copyDirs = ["Afgeleiden",
                       "Rapportages_meetresultaten",
                       "Rapportages_onregelmatigheden",
                       "rapporten HeronQAE TC 5"]
        # No processing of concordance tables
        wf.processCTables = False
    elif workflow == "tifftojp2-generic":
        # Generic workflow - input batch only contains TIFF images
        wf = tifftojp2_generic.Workflow()
        # Compression profile
        wf.compressionProfile = "KB_MASTER_LOSSLESS_10/06/2026"
        # Schematron schema used for properties check
        wf.schema = "kbMaster_2026.sch"
        # No processing of concordance tables
        wf.processCTables = False
    elif workflow == "tifftojp2-generic-convertpaletted":
        # Generic workflow - input batch only contains TIFF images
        # Convert any paletted TIFFs to (temporary) "normal" TIFF
        # before converting to JP2, to prevent paletted JP2s
        wf = tifftojp2_generic.Workflow()
        # Compression profile
        wf.compressionProfile = "KB_MASTER_LOSSLESS_10/06/2026"
        # Schematron schema used for properties check
        wf.schema = "kbMaster_2026.sch"
        # No processing of concordance tables
        wf.processCTables = False
        # Convert paletted images to regular colorspace
        wf.convertPalettedImages = True

    # Check if compression profile exists
    profileExists = False
    for profile in cprofilesDict["compressionProfiles"]:
        if profile["name"] == wf.compressionProfile:
            profileExists = True
    if not profileExists:
        msg = "compression profile ({}) is undefined".format(wf.compressionProfile)
        shared.errorExit(msg)

    # Check if schema exists
    schema = os.path.join(configPath, "schemas", wf.schema)
    if not os.path.isfile(schema):
        msg = "schema ({}) does not exist".format(schema)
        shared.errorExit(msg)

    wf.dirIn = dirIn
    wf.dirOut = dirOut
    wf.configPath = configPath
    wf.configDict = configDict
    wf.cprofilesDict = cprofilesDict
    wf.processBatch()

    # Timing output
    end = time.time()
    logging.info("kbiw ended: {}".format(time.asctime()))
    # Elapsed time (seconds)
    timeElapsed = end - start
    timeInMinutes = round((timeElapsed / 60), 2)
    logging.info("Elapsed time: {} minutes".format(timeInMinutes))


if __name__ == "__main__":
    main()
