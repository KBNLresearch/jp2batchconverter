#! /usr/bin/env python3
"""Module for manipulating and checking of concordance tables
in Middeleeuwse Handschriften batches"""

import os
import csv
import logging


class CTables:
    """Concordance tables class"""

    def __init__(self, dirConcordanceIn, dirIn, dirOut, delimiterIn,
                 delimiterOut, extensionsIn, batchManifest):

        self.noErrors = 0
        self.noWarnings = 0
        self.dirConcordanceIn = dirConcordanceIn
        self.dirIn = dirIn
        self.dirOut = dirOut
        self.delimiterIn = delimiterIn
        self.delimiterOut = delimiterOut
        self.extensionsIn = extensionsIn
        self.batchManifest = batchManifest
        self.dirConcordanceOut = None

    def update(self):
        """Update concordance tables"""

        dirPathInRel = os.path.relpath(self.dirConcordanceIn, start=self.dirIn)
        dirPathIn = os.path.abspath(os.path.join(self.dirIn, dirPathInRel))
        self.dirConcordanceOut = os.path.abspath(
            os.path.join(self.dirOut, dirPathInRel))

        # Create output directory
        if not os.path.isdir(self.dirConcordanceOut):
            os.makedirs(self.dirConcordanceOut)

        files = os.listdir(dirPathIn)
        for f in files:
            fileIn = os.path.join(dirPathIn, f)
            fileOut = os.path.join(self.dirConcordanceOut, f)
            fileExtension = os.path.splitext(f)[1]
            fileExtension = fileExtension.upper().strip('.')

            if os.path.isfile(fileIn) and fileExtension == "CSV":
                self.updateCTable(fileIn, fileOut)

    def updateCTable(self, fileIn, fileOut):
        """Update one concordance table. For each image file, it adds the full path,
        which is inferred from the name of the concordance table file (master, access)
        or the name of the image file (target). For images with a file extension that matches
        self.extensionsIn, the file extension is changed to jp2"""

        listOut = []
        rowIndex = 0
        logging.info(
            "updating concordance table {} to {}".format(fileIn, fileOut))

        # First part of concordance table name refers to corresponding directory in "Signaturen"
        sigDir = os.path.basename(fileIn).split("_")[0]
        masterDirPath = os.path.join("Signaturen", sigDir, "Master")
        accessDirPath = os.path.join("Signaturen", sigDir, "Access_Renamed")

        with open(fileIn, 'r', newline='', encoding='utf-8') as fIn:
            reader = csv.reader(fIn, delimiter=self.delimiterIn)
            cTabIn = list(reader)

        for row in cTabIn:
            if rowIndex == 0:
                # Header line
                listOut.append(row)
                rowIndex += 1
            else:
                rowOut = []
                colIndex = 0
                for fNameIn in row:
                    # Flag that indicates empty values
                    emptyFlag = False

                    if fNameIn == "":
                        emptyFlag = True
                        logging.warning("empty entry in concordance table {}, (column '{}')".format(fileIn, headerValue))
                        self.noWarnings += 1
                    if not emptyFlag:
                        # Header value
                        headerValue = (cTabIn[0][colIndex])
                        # File prefix and extension
                        pre, ext = os.path.splitext(fNameIn)
                        ext = ext.strip(".").upper()

                        # Update file extension if needed
                        if ext in self.extensionsIn:
                            fNameOut = "{}.{}".format(pre, "jp2")
                        else:
                            fNameOut = fNameIn

                        # Add path
                        if headerValue == "Master":
                            fOut = os.path.join(masterDirPath, fNameOut)

                        elif headerValue == "Access_Renamed":
                            fOut = os.path.join(accessDirPath, fNameOut)

                        elif headerValue.startswith("Targets"):
                            # Target location follows from file base name
                            try:
                                nameComponents = pre.split("_")
                            except IndexError:
                                nameComponents = []
                            try:
                                targetDir = "{}_{}_{}".format(
                                    nameComponents[0], nameComponents[2], nameComponents[3])
                            except IndexError:
                                targetDir = ""
                                logging.error("couldn't construct directory path for target {}".format(fNameOut))
                            fOut = os.path.join("Targets", targetDir, fNameOut)
                        else:
                            logging.warning("unknown header value '{}' in concordance table {}".format(headerValue, fileIn))
                            self.noWarnings += 1

                        rowOut.append(fOut)
                    if emptyFlag:
                        rowOut.append("")

                    colIndex += 1

                rowIndex += 1

                listOut.append(rowOut)

        try:
            with open(fileOut, 'w', newline='', encoding='utf-8') as fOut:
                writer = csv.writer(fOut, delimiter=self.delimiterOut)
                writer.writerows(listOut)
        except Exception:
            logging.error(
                "couldn't write updated concordance table to {}".format(fileOut))
            self.noErrors += 1

    def verify(self):
        """Cross-check concordance tables against batch manifest (including reverse check)"""

        logging.info("Verifying concordance tables against batch manifest")

        with open(self.batchManifest, 'r', newline='', encoding='utf-8') as fMan:
            reader = csv.reader(fMan, delimiter=self.delimiterOut)
            manifestData = list(reader)

        # List that will store all image references in the batch manifest
        imagesManifest = []

        # List that will store all image references in all concordance tables
        imagesAllCTables = []
        rowIndex = 0
        for row in manifestData:
            if rowIndex > 0:
                imagesManifest.append(row[0])
            rowIndex += 1

        # Stop here if concordance dir doesn't exist
        if not os.path.isdir(self.dirConcordanceOut):
            logging.error("concordance directory {} does not exist".format(
                self.dirConcordanceOut))
            self.noErrors += 1
            return
        cTables = os.listdir(self.dirConcordanceOut)
        for cTable in cTables:
            cTable = os.path.join(self.dirConcordanceOut, cTable)
            with open(cTable, 'r', newline='', encoding='utf-8') as fCTab:
                reader = csv.reader(fCTab, delimiter=self.delimiterOut)
                cTabData = list(reader)

            # List that will store all image references in this concordance table
            imagesCTable = []

            rowIndex = 0
            colIndex = 0
            for row in cTabData:
                if rowIndex > 0:
                    for col in row:
                        if col != "":
                            # Skip empty records
                            imagesCTable.append(col)
                        colIndex += 1
                rowIndex += 1

            for image in imagesCTable:
                # Check against batch manifest
                if image not in imagesManifest:
                    logging.error(
                        "image {} not found in batch manifest".format(image))
                    self.noErrors += 1
                # Add image to combined list of image references from all concordance tables
                imagesAllCTables.append(image)

        # Reverse check
        for image in imagesManifest:
            if image not in imagesAllCTables:
                logging.error(
                    "image {} from batch manifest not referenced in any concordance table".format(image))
                self.noErrors += 1
