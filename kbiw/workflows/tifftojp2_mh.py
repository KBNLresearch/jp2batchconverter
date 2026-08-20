#! /usr/bin/env python3

"""
TIFF to JP2 workflow for KB Middeleeuwse Handschriften batches
"""

import sys
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
        # Flag that activates automatic conversion of paletted input images to a regular colorspace
        self.convertPalettedImages = False


    def processBatch(self):
        """Process a batch"""

        # Convert list of input file extensions to upper case
        self.extensionsIn = [extension.upper()
                             for extension in self.extensionsIn]

        # Add path to Schematron schema for properties check
        self.schema = os.path.join(self.configPath, "schemas", self.schema)

        # Create TiffToJP2 class instance
        self.tifftoJP2Instance = tifftojp2.TiffToJP2()
        self.tifftoJP2Instance.configDict = self.configDict
        self.tifftoJP2Instance.cprofilesDict = self.cprofilesDict
        self.tifftoJP2Instance.compressionProfile = self.compressionProfile
        self.tifftoJP2Instance.schema = self.schema
        self.tifftoJP2Instance.noErrors = self.noErrors
        self.tifftoJP2Instance.noWarnings = self.noWarnings
        self.tifftoJP2Instance.dirIn = self.dirIn
        self.tifftoJP2Instance.dirOut = self.dirOut
        self.tifftoJP2Instance.grokInstance = self.grokInstance
        self.tifftoJP2Instance.etInstance = self.etInstance
        self.tifftoJP2Instance.vipsInstance = self.vipsInstance
        self.tifftoJP2Instance.convertPalettedImages = self.convertPalettedImages
        self.tifftoJP2Instance.configure()

        # Create "Checksums" directory
        self.dirChecksums = os.path.join(self.dirOut, "Checksums")
        if not os.path.isdir(self.dirChecksums):
            try:
                os.makedirs(self.dirChecksums)
            except exception:
                msg = "creation of Checksums directory {} failed".format(self.dirChecksums)
                shared.errorExit(msg)

        # Create "Pakbon" directory
        dirPakbon = os.path.join(self.dirOut, "Pakbon")
        if not os.path.isdir(dirPakbon):
            try:
                os.makedirs(dirPakbon)
            except exception:
                msg = "creation of Pakbon directory {} failed".format(dirPakbon)
                shared.errorExit(msg)

        # Add paths to batch manifest, summary and checksum files
        self.batchManifest = os.path.join(dirPakbon, self.batchManifest)
        self.summaryFile = os.path.join(dirPakbon, self.summaryFile)
        self.checksumFile = os.path.join(self.dirChecksums, self.checksumFile)

        # Remove any previous batch manifest / checksum / summary file instances
        if os.path.isfile(self.batchManifest):
            os.remove(self.batchManifest)
        if os.path.isfile(self.summaryFile):
            os.remove(self.summaryFile)
        if os.path.isfile(self.checksumFile):
            os.remove(self.checksumFile)

        # Write header to batch manifest
        manifestHeadings = ["image",
                            "successGrok",
                            "successExifTool",
                            "palettedImage",
                            "successPixelCheck",
                            "successJpylyzerCheck",
                            "failedJpylyzerChecks",
                            "succesFileMatch",
                            "succesChecksumCheck"]

        with open(self.batchManifest, 'w', newline='', encoding='utf-8') as fManifest:
            writer = csv.writer(fManifest, delimiter=self.delimiterOut)
            writer.writerow(manifestHeadings)

        # Write header to checksum file
        checksumHeadings = ["File",
                            "SHA512"]

        with open(self.checksumFile, 'w', newline='', encoding='utf-8') as fChecksum:
            writer = csv.writer(fChecksum, delimiter=self.delimiterOut)
            writer.writerow(checksumHeadings)

        # Iterate over directories and files in batch
        for dirname, dirnames, filenames in os.walk(self.dirIn):
            for subdirname in dirnames:
                thisDirectory = os.path.join(dirname, subdirname)

                if subdirname == "Access_Renamed":
                    # Access JPEGs are copied without modification
                    # Checksums are verified against checksum file in source batch
                    self.copyAccessDir(thisDirectory)

                if subdirname == "Pakbon":
                    # Files in Pakbon directory - TODO
                    pass

                if subdirname == "Concordantie":
                    # Update concordance tables
                    myCTables = ctables.CTables(thisDirectory,
                                                self.dirIn,
                                                self.dirOut,
                                                self.delimiterIn,
                                                self.delimiterOut,
                                                self.extensionsIn,
                                                self.batchManifest)
                    myCTables.update()

            ## TEST
            #sys.exit()

            for filename in filenames:
                self.processFile(filename, dirname)

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
            fSum.write("Grok version: {}\n".format(self.tifftoJP2Instance.grokInstance.version))
            fSum.write("Errors: {}\n".format(self.noErrors))
            fSum.write("Warnings: {}\n".format(self.noWarnings))
            fSum.write(
                "See batch manifest and log file for details on errors and warnings\n")


    def processFile(self, filename, dirname):
        """Process one file """
        if filename.startswith("._"):
            # Ignore AppleDouble resource fork files (identified here by name)
            pass
        else:
            thisFile = os.path.join(dirname, filename)
            thisExtension = os.path.splitext(thisFile)[1]
            thisExtension = thisExtension.upper().strip('.')
            if thisExtension in self.extensionsIn:
                # Convert image and perform quality checks
                self.tifftoJP2Instance.convertImage(thisFile)
                self.noErrors += self.tifftoJP2Instance.noErrors
                self.noWarnings += self.tifftoJP2Instance.noWarnings

                # Write row to batch manifest
                with open(self.batchManifest, 'a', newline='', encoding='utf-8') as fManifest:
                    writer = csv.writer(fManifest, delimiter=self.delimiterOut)
                    # add two empy columns to fit access fields
                    rowBm = self.tifftoJP2Instance.rowBm
                    rowBm.extend(["na","na"])
                    writer.writerow(rowBm)

                # Write row to checksum file
                with open(self.checksumFile, 'a', newline='', encoding='utf-8') as fChecksum:
                    writer = csv.writer(fChecksum, delimiter=self.delimiterOut)
                    writer.writerow([self.tifftoJP2Instance.rowBm[0], self.tifftoJP2Instance.checksum])


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


    def copyAccessDir(self, dirIn):
        """Copy dir with access image to output batch and verify checksums"""

        foundInputChecksumFile = False

        # Find input access checksums file based on naming pattern
        dirChecksumsIn = os.path.join(self.dirIn, "Checksums")
        for file in os.listdir(dirChecksumsIn):
            if file.endswith("Signaturen_access_renamed_checksum_sha512.csv"):
                fileAccessChecksums = os.path.join(dirChecksumsIn, file)
                foundInputChecksumFile = True

        if foundInputChecksumFile:
            with open(fileAccessChecksums, newline='') as fCA:
                reader = csv.reader(fCA, delimiter=",")
                accessChecksums = list(reader)
        else:
            logging.error("missing checksum file for access images in input batch")
            self.noErrors += 1

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

        # Iterate over files
        for dirname, dirnames, filenames in os.walk(dirPathOut):
            for filename in filenames:
                if filename.startswith("._"):
                    # Ignore AppleDouble resource fork files (identified here by name)
                    pass
                else:
                    thisFile = os.path.join(dirname, filename)
                    # File reference, relative to output directory
                    thisFileRel = os.path.relpath(thisFile, start=self.dirOut)
                    # Calculate checksum (SHA-512)
                    checksum = shared.generate_file_sha512(thisFile)

                    # Write row to checksum file
                    with open(self.checksumFile, 'a', newline='', encoding='utf-8') as fChecksum:
                        writer = csv.writer(fChecksum, delimiter=self.delimiterOut)
                        writer.writerow([thisFileRel, checksum])

                    fileMatch = False
                    checksumMatch = False

                    if foundInputChecksumFile:
                        # Verify checksum against checksum in input batch
                        for row in accessChecksums:
                            if row[0] == thisFileRel:
                                fileMatch = True
                                if checksum == row[1]:
                                    checksumMatch = True

                    if not fileMatch:
                        logging.error("no matching record in checksum file for {}".format(thisFileRel))
                        self.noErrors += 1
                    if not checksumMatch:
                        logging.error("checksum check unsuccessful for {}".format(thisFileRel))
                        self.noErrors += 1

                    # Write row to batch manifest
                    with open(self.batchManifest, 'a', newline='', encoding='utf-8') as fManifest:
                        writer = csv.writer(fManifest, delimiter=self.delimiterOut)
                        rowBm = [thisFileRel, "na", "na", "na", "na", "na", "na", fileMatch, checksumMatch]
                        writer.writerow(rowBm)

