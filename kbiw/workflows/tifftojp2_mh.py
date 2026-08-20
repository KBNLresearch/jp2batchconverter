#! /usr/bin/env python3

"""
TIFF to JP2 workflow for KB Middeleeuwse Handschriften batches
"""

import os
import shutil
import csv
import logging
from .. import tifftojp2
from .. import shared
from .. import ctables


class Workflow:
    """workflow class"""

    def __init__(self):
        """initialise workflow class instance"""
        # List of input extensions that will be converted to JP2
        self.extensionsIn = ["tif", "tiff"]
        # Compression profile (name only, path is added later)
        self.compressionProfile = "KB_MASTER_LOSSLESS_10/06/2026"
        # Schematron schema used for properties check
        self.schema = "kbMaster_2026.sch"
        # Delimiter used in input concordance tables
        self.delimiterIn = ";"
        # Delimiter used in summary file and output concordance tables
        self.delimiterOut = ";"
        # Batch manifest (name only, path is added later)
        self.batchManifest = "manifest.csv"
        # Summary file (name only, path is added later)
        self.summaryFile = "summary.txt"
        # Checksum file (name only, path is added later)
        self.checksumFile = "checksums_sha512.csv"
        # Number of errors encountered during workflow
        self.noErrors = 0
        # Number of warnings encountered during workflow
        self.noWarnings = 0
        # Input batch directory (set in main kbiw.py module)
        self.dirIn = None
        # Output batch directory (set in main kbiw.py module)
        self.dirOut = None
        # Configuration path (set in main kbiw.py module)
        self.configPath = None
        # Configuration dictionary (set in main kbiw.py module)
        self.configDict = None
        # Compression profiles dictionary (set in main kbiw.py module)
        self.cprofilesDict = None
        # Grok instance (set in processBatch function)
        self.grokInstance = None
        # ExifTool instance (set in processBatch function)
        self.etInstance = None
        # Vips instance (set in processBatch function)
        self.vipsInstance = None
        # Flag that activates processing of concordance tables
        self.processCTables = True
        # Name of directory that contains concordance tables
        self.cTableDirName = "Concordantie"
        # Flag that activates automatic conversion of paletted input images to a regular colorspace
        self.convertPalettedImages = False
        # List of directory names that will copied unchanged from input to output batch
        self.copyDirs = ["Pakbon",
                       "Access_Renamed"]

    def processBatch(self):
        """Process a batch"""

        # Convert list of input file extensions to upper case
        self.extensionsIn = [extension.upper()
                             for extension in self.extensionsIn]

        # Add path to Schematron schema for properties check
        self.schema = os.path.join(self.configPath, "schemas", self.schema)

        # Create TiffToJP2 class instance
        tifftoJP2Instance = tifftojp2.TiffToJP2()
        tifftoJP2Instance.configDict = self.configDict
        tifftoJP2Instance.cprofilesDict = self.cprofilesDict
        tifftoJP2Instance.compressionProfile = self.compressionProfile
        tifftoJP2Instance.schema = self.schema
        tifftoJP2Instance.noErrors = self.noErrors
        tifftoJP2Instance.noWarnings = self.noWarnings
        tifftoJP2Instance.dirIn = self.dirIn
        tifftoJP2Instance.dirOut = self.dirOut
        tifftoJP2Instance.grokInstance = self.grokInstance
        tifftoJP2Instance.etInstance = self.etInstance
        tifftoJP2Instance.vipsInstance = self.vipsInstance
        tifftoJP2Instance.convertPalettedImages = self.convertPalettedImages
        tifftoJP2Instance.configure()

        # Create "Pakbon" directory
        dirPakbon = os.path.join(self.dirOut, "Pakbon")
        if not os.path.isdir(dirPakbon ):
            try:
                os.makedirs(dirPakbon )
            except exception:
                msg = "creation of Pakbon directory {} failed".format(dirPakbon)
                shared.errorExit(msg)

        # Add paths to batch manifest, checksum and summary files
        self.batchManifest = os.path.join(dirPakbon, self.batchManifest)
        self.checksumFile = os.path.join(dirPakbon, self.checksumFile)
        self.summaryFile = os.path.join(dirPakbon, self.summaryFile)

        # Remove any previous batch manifest / checksum / summary file instances
        if os.path.isfile(self.batchManifest):
            os.remove(self.batchManifest)
        if os.path.isfile(self.checksumFile):
            os.remove(self.checksumFile)
        if os.path.isfile(self.summaryFile):
            os.remove(self.summaryFile)

        # Write header to batch manifest
        manifestHeadings = ["image",
                            "successGrok",
                            "successExifTool",
                            "palettedImage",
                            "successPixelCheck",
                            "successJpylyzerCheck",
                            "failedJpylyzerChecks"]

        with open(self.batchManifest, 'w', newline='', encoding='utf-8') as fManifest:
            writer = csv.writer(fManifest, delimiter=self.delimiterOut)
            writer.writerow(manifestHeadings)

        # Iterate over directories and files in batch
        for dirname, dirnames, filenames in os.walk(self.dirIn):
            for subdirname in dirnames:
                thisDirectory = os.path.join(dirname, subdirname)
                if subdirname in self.copyDirs:
                    # Files in copyDirs directories are copied without modification
                    self.copyDir(thisDirectory)
                if self.processCTables:
                    if subdirname == self.cTableDirName:
                        # Update concordance tables
                        myCTables = ctables.CTables(thisDirectory,
                                                    self.dirIn,
                                                    self.dirOut,
                                                    self.delimiterIn,
                                                    self.delimiterOut,
                                                    self.extensionsIn,
                                                    self.batchManifest)
                        myCTables.update()

            for filename in filenames:
                if filename.startswith("._"):
                    # Ignore AppleDouble resource fork files (identified here by name)
                    pass
                else:
                    thisFile = os.path.join(dirname, filename)
                    thisExtension = os.path.splitext(thisFile)[1]
                    thisExtension = thisExtension.upper().strip('.')
                    if thisExtension in self.extensionsIn:
                        # Convert image and perform quality checks
                        tifftoJP2Instance.convertImage(thisFile)
                        self.noErrors += tifftoJP2Instance.noErrors
                        self.noWarnings += tifftoJP2Instance.noWarnings

                        # Write row to batch manifest
                        with open(self.batchManifest, 'a', newline='', encoding='utf-8') as fManifest:
                            writer = csv.writer(fManifest, delimiter=self.delimiterOut)
                            writer.writerow(tifftoJP2Instance.rowBm)

                        # Construct checksum line, following https://superuser.com/a/1566139/681049
                        checksumLine = "{}  {}\n".format(tifftoJP2Instance.checksum, tifftoJP2Instance.rowBm[0])

                        # Write checksum line to file
                        with open(self.checksumFile, 'a', newline='', encoding='utf-8') as fC:
                            fC.write(checksumLine)

        if self.processCTables:
            # Cross check entries in concordance tables with batch manifest
            try:
                myCTables.verify()

                # Add any errors from concordance updating / checking to general error count
                self.noErrors += myCTables.noErrors
            except UnboundLocalError:
                # We end up here if myCtables is undefined
                logging.error("no concordance tables found in batch")
                self.noErrors += 1

        # Number of errors, warnings to log
        logging.info("workflow completed with {} errors and {} warnings".format(
            self.noErrors, self.noWarnings))

        # Write summary file
        with open(self.summaryFile, 'w', newline='', encoding='utf-8') as fSum:
            fSum.write("Grok version: {}\n".format(tifftoJP2Instance.grokInstance.version))
            fSum.write("Errors: {}\n".format(self.noErrors))
            fSum.write("Warnings: {}\n".format(self.noWarnings))
            fSum.write(
                "See batch manifest and log file for details on errors and warnings\n")

    def copyDir(self, dirIn):
        """Copy input dir to same relative location in output batch"""

        dirPathInRel = os.path.relpath(dirIn, start=self.dirIn)
        dirPathIn = os.path.abspath(os.path.join(self.dirIn, dirPathInRel))
        dirPathOut = os.path.abspath(os.path.join(self.dirOut, dirPathInRel))
        logging.info("copying directory {} to {}".format(
            dirPathIn, dirPathOut))
        try:
            shutil.copytree(dirPathIn, dirPathOut, dirs_exist_ok=True)
        except Exception:
            logging.error("copying data from directory {} to {} resulted in an exception".format(
                dirPathIn, dirPathOut))
            self.noErrors += 1
