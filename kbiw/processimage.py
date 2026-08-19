#! /usr/bin/env python3

"""KB Image Workflow Tool

Johan van der Knijff

Copyright 2026, KB/National Library of the Netherlands

"""

import os
import shutil
import csv
import logging
import exiftool
from . import shared
from . import grok
from . import vips
from . import propertiescheck

class processImage:
    """image processing class"""

    def __init__(self):
        """initialise workflow class instance"""
        # Compression profile
        self.compressionProfile = None
        # Schematron schema used for properties check
        self.schema = None
        # Number of errors encountered during workflow
        self.noErrors = 0
        # Number of warnings encountered during workflow
        self.noWarnings = 0
        # Input batch directory
        self.dirIn = None
        # Output batch directory
        self.dirOut = None
        # Configuration dictionary
        self.configDict = None
        # Compression profiles dictionary
        self.cprofilesDict = None
        # Grok instance
        self.grokInstance = None
        # ExifTool instance
        self.etInstance = None
        # Vips instance
        self.vipsInstance = None
        # Flag that activates automatic conversion of paletted input images to a regular colorspace
        self.convertPalettedImages = False
        # Grok version string
        self.grokVersion = None

    def configure(self):
        # Start Grok class instance
        self.grokInstance = grok.Grok()
        self.grokInstance.configDict = self.configDict
        self.grokInstance.cprofilesDict = self.cprofilesDict
        self.grokInstance.configure()
        logging.info("grk_compress version: {}".format(
            self.grokInstance.version))
        self.grokInstance.compressionProfile = self.compressionProfile
        self.grokVersion = self.grokInstance.version

        # Start ExifTool instance, using executables as defined in configuration file
        self.etInstance = exiftool.ExifToolHelper(
            executable=self.configDict["exifToolExecutable"])

        # Start Vips instance
        self.vipsInstance = vips.Vips(self.configDict["vipsBinDir"])


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

            # File reference, relative to output directory
            fileOutRel = os.path.relpath(fileOut, start=self.dirOut)
            # Calculate checksum (SHA-512)
            checksum = shared.generate_file_sha512(fileOut)

            # Batch manifest row
            rowBm = [fileOutRel,
                successGrok,
                successExifTool,
                pallettedFlag,
                successPixelCheck,
                successJpylyzerCheck,
                schTestsFailedStr]

        return rowBm, checksum
