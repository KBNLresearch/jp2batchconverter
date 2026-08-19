#! /usr/bin/env python3

"""
TIFF to JP2 workflow
"""

import os
import shutil
import csv
import logging
import exiftool
from .. import processimage
from .. import shared
from .. import grok
from .. import vips
from .. import propertiescheck
from .. import ctables


class workflow:
    """workflow class"""

    def __init__(self):
        """initialise workflow class instance"""
        # List of input extensions that will be converted to JP2
        self.extensionsIn = ["tif", "tiff"]
        # Compression profile (name only, path is added later)
        self.compressionProfile = None
        # Schematron schema used for properties check
        self.schema = None
        # Delimiter used in input concordance tables
        self.delimiterIn = ";"
        # Delimiter used in summary file and output concordance tables
        self.delimiterOut = ";"
        # Batch manifest (name only, path is added later)
        self.batchManifest = "manifest.csv"
        # Summary file (name only, path is added later)
        self.summaryFile = "summary.txt"
        # Checksum file (name only, path is added later)
        self.checksumFile = "checksums.sha512"
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
        self.processCTables = False
        # Name of directory that contains concordance tables
        self.cTableDirName = None
        # Flag that activates automatic conversion of paletted input images to a regular colorspace
        self.convertPalettedImages = False
        # List of directory names that will copied unchanged from input to output batch
        self.copyDirs = []

    def processBatch(self):
        """Process a batch"""

        # Convert list of input file extensions to upper case
        self.extensionsIn = [extension.upper()
                             for extension in self.extensionsIn]

        # Add path to Schematron schema for properties check
        self.schema = os.path.join(self.configPath, "schemas", self.schema)

        # Start Grok class instance
        self.grokInstance = grok.Grok()
        self.grokInstance.configDict = self.configDict
        self.grokInstance.cprofilesDict = self.cprofilesDict
        self.grokInstance.configure()
        logging.info("grk_compress version: {}".format(
            self.grokInstance.version))
        self.grokInstance.compressionProfile = self.compressionProfile

        # Start ExifTool instance, using executables as defined in configuration file
        self.etInstance = exiftool.ExifToolHelper(
            executable=self.configDict["exifToolExecutable"])

        # Start Vips instance
        self.vipsInstance = vips.Vips(self.configDict["vipsBinDir"])

        # Create procesImage class instance
        processImageInstance = processimage.processImage()
        processImageInstance.schema = self.schema
        processImageInstance.delimiterOut = self.delimiterOut
        processImageInstance.batchManifest = self.batchManifest
        processImageInstance.checksumFile = self.checksumFile
        processImageInstance.noErrors = self.noErrors
        processImageInstance.noWarnings = self.noWarnings
        processImageInstance.dirIn = self.dirIn
        processImageInstance.dirOut = self.dirOut
        processImageInstance.grokInstance = self.grokInstance
        processImageInstance.etInstance = self.etInstance
        processImageInstance.vipsInstance = self.vipsInstance
        processImageInstance.convertPalettedImages = self.convertPalettedImages

        # Add paths to batch manifest, checksum and summary files
        self.batchManifest = os.path.join(self.dirOut, self.batchManifest)
        self.checksumFile = os.path.join(self.dirOut, self.checksumFile)
        self.summaryFile = os.path.join(self.dirOut, self.summaryFile)

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
                        processImageInstance.processImage(thisFile)
                        self.noErrors += processImageInstance.noErrors
                        self.noWarnings += processImageInstance.noWarnings

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
            fSum.write("Grok version: {}\n".format(self.grokInstance.version))
            fSum.write("Errors: {}\n".format(self.noErrors))
            fSum.write("Warnings: {}\n".format(self.noWarnings))
            fSum.write(
                "See batch manifest and log file for details on errors and warnings\n")

    def processImage(self, fileIn):
        """Process one image"""
        convertFromUnpaletted = False
        successGrok = False
        successExifTool = False
        successPixelCheck = False
        successJpylyzerCheck = False
        schTestsFailedStr = ""
        fileNameIn = os.path.basename(fileIn)
        filePathIn = os.path.dirname(fileIn)
        filePathInRel = os.path.relpath(filePathIn, start=self.dirIn)
        filePathOut = os.path.abspath(os.path.join(self.dirOut, filePathInRel))

        # Create filePathOut if it doesn't exist (including any missing parent dirs)
        if not os.path.isdir(filePathOut):
            os.makedirs(filePathOut)

        # Construct name for output file
        pre, ext = os.path.splitext(fileNameIn)
        fileNameOut = "{}.{}".format(pre, "jp2")

        fileOut = os.path.abspath(os.path.join(filePathOut, fileNameOut))

        logging.info("#############################")
        logging.info("Input image: {}".format(fileIn))
        logging.info("Output image: {}".format(fileOut))

        if self.convertPalettedImages:
            try:
                exiftmp = self.etInstance.get_tags(
                    fileIn, "IFD0:PhotometricInterpretation")
                PhotometricInterpretation = exiftmp[0]["EXIF:PhotometricInterpretation"]
                logging.info("PhotometricInterpretation: {}".format(
                    PhotometricInterpretation))
                if PhotometricInterpretation == 3:
                    convertFromUnpaletted = True
                    logging.info("found paletted input image")
                    fTmp = os.path.abspath(
                        os.path.join(self.dirOut, "kbiwtmp.tif"))
                    pcSuccess = self.vipsInstance.convertPaletted(fileIn, fTmp)
                    logging.info(
                        "palette conversion successful: {}".format(pSuccess))
            except:
                logging.warning(
                    "ExifTool couldn't extract IFD0:PhotometricInterpretation tag")
                self.noWarnings += 1

        # Pass I/O to Grok instance and run the conversion
        if convertFromUnpaletted and pcSuccess:
            # Use unpalletted image as input
            self.grokInstance.imageIn = fTmp
        else:
            self.grokInstance.imageIn = fileIn
        self.grokInstance.jp2Out = fileOut

        self.grokInstance.compress()
        logging.info("grk_compress exit status: {}".format(
            self.grokInstance.status))
        if self.grokInstance.status == 0:
            successGrok = True
            logging.info("grok.compress completed successfully")
        elif self.grokInstance.status != 0:
            logging.error("abnormal grk_compress exit status")
            self.noErrors += 1
        if not self.grokInstance.success:
            logging.error("grok.compress function resulted in an exception")
            self.noErrors += 1

        logging.info("grk_compress stdout: {}".format(self.grokInstance.out))
        logging.info("grk_compress stderr: {}".format(
            self.grokInstance.errors))

        if convertFromUnpaletted and pcSuccess:
            # Remove temporary file
            try:
                os.remove(fTmp)
            except Exception:
                logging.warning(
                    "couldn't remove temporary file {}".format(fTmp))
                self.noWarnings += 1

        if successGrok:

            # Read metadata from input TIFF and write as XMP block to JP2
            # Adapted from: https://exiftool.org/forum/index.php?topic=2922.0
            try:
                self.etInstance.execute("-tagsfromfile",
                                        fileIn,
                                        "-all>xmp:all",
                                        "-overwrite_original",
                                        fileOut)
                successExifTool = True
                logging.info("copied metadata from TIFF to JP2")
            except Exception:
                logging.error(
                    "ExifTool failed to copy metadata from TIFF to JP2")
                successExifTool = False
                self.noErrors += 1

            # Analyze JP2 with Jpylyzer and evaluate output against Schematron policy
            status, schTestsFailed, jpTestsFailed, pallettedFlag = propertiescheck.propertiesCheck(
                fileOut, self.schema)

            if status == "pass":
                successJpylyzerCheck = True
                logging.info("image conforms to Schematron rules")
            else:
                # Add failed tests to pipe-delimited string that is included in summary file
                schTestsFailedOut = []
                for schtest in schTestsFailed:
                    schTestsFailedOut.append(schtest[0])

                schTestsFailedStr = '|'.join(schTestsFailedOut)
                logging.warning("image does not conform to Schematron rules")
                self.noWarnings += 1

            try:
                # Check on pixel values (skip for paletted images, because LibVips can't handle paletted JP2s)
                if not pallettedFlag:
                    ssDiff = self.vipsInstance.sumSqDiff(fileIn, fileOut)
                    if ssDiff == None:
                        logging.error("pixel check failed with exception")
                        self.noErrors += 1
                    if ssDiff == 0:
                        logging.info(
                            "pixel values of input and output images are identical")
                        successPixelCheck = True
                    else:
                        logging.warning(
                            "pixel values of input and output images are not identical")
                        self.noWarnings += 1
                    logging.info(
                        "Sum of squared pixel differences: {}".format(ssDiff))
                else:
                    ssDiff = None
                    logging.warning("paletted image, skipped pixel check")
                    self.noWarnings += 1

            except Exception:
                logging.error("pixel check failed")
                ssDiff = None
                self.noErrors += 1

            # Calculate checksum (SHA-512)
            checksum = shared.generate_file_sha512(fileOut)

            # File reference, relative to output directory
            fileOutRel = os.path.relpath(fileOut, start=self.dirOut)

            # Construct checksum line, following https://superuser.com/a/1566139/681049
            checksumLine = "{}  {}\n".format(checksum, fileOutRel)

            # Write checksum line to file
            with open(self.checksumFile, 'a', newline='', encoding='utf-8') as fC:
                fC.write(checksumLine)

        # Write outcomes of QA checks to batch manifest
        with open(self.batchManifest, 'a', newline='', encoding='utf-8') as fManifest:
            writer = csv.writer(fManifest, delimiter=self.delimiterOut)
            row = [fileOutRel,
                   successGrok,
                   successExifTool,
                   pallettedFlag,
                   successPixelCheck,
                   successJpylyzerCheck,
                   schTestsFailedStr]
            writer.writerow(row)

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
