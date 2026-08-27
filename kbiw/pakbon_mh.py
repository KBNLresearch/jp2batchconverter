#! /usr/bin/env python3
"""Module for updating Pakbon file in
in Middeleeuwse Handschriften batches"""

import os
import xml.etree.ElementTree as ET
import logging

class Pakbon:
    """Pakbon class"""

    def __init__(self, dirIn, dirOut):

        self.noErrors = 0
        self.dirIn = dirIn
        self.dirOut = dirOut

    def writePakbon(self):
        """Write pakbon file, based on pakbon in source batch and file statistics of destination batch """

        # Initial values of output stats
        numberOfFilesMaster = 0
        totalFileSizeMaster = 0
        numberOfFilesAccess = 0
        totalFileSizeAccess = 0
        numberOfFilesConcordantie = 0
        totalFileSizeConcordantie = 0
        numberOfFilesTargets = 0
        totalFileSizeTargets = 0
        numberOfFilesChecksums = 0
        totalFileSizeChecksums = 0
        averageFileSize = 0
        averageFileSizeMaster = 0
        averageFileSizeAccess = 0
        averageFileSizeConcordantie = 0
        averageFileSizeTargets = 0
        averageFileSizeChecksums = 0

        # Iterate over directories and files in output batch
        for dirname, dirnames, filenames in os.walk(self.dirOut):
            for subdirname in dirnames:
                thisDirectory = os.path.join(dirname, subdirname)

                if subdirname == "Master":
                    #files = os.listdir(thisDirectory)
                    files = [f for f in os.listdir(thisDirectory) if os.path.isfile(os.path.join(thisDirectory, f))]
                    for file in files:
                        filePath = os.path.join(thisDirectory, file)
                        fileSize = os.path.getsize(filePath)
                        numberOfFilesMaster += 1
                        totalFileSizeMaster += fileSize

                if subdirname == "Access_Renamed":
                    files = [f for f in os.listdir(thisDirectory) if os.path.isfile(os.path.join(thisDirectory, f))]
                    for file in files:
                        filePath = os.path.join(thisDirectory, file)
                        fileSize = os.path.getsize(filePath)
                        numberOfFilesAccess += 1
                        totalFileSizeAccess += fileSize

                if subdirname == "Targets":
                    dirs = [d for d in os.listdir(thisDirectory) if os.path.isdir(os.path.join(thisDirectory, d))]
                    for dir in dirs:
                        dirTarget = os.path.join(thisDirectory, dir)
                        files = [f for f in os.listdir(dirTarget) if os.path.isfile(os.path.join(dirTarget, f))]
                        for file in files:
                            filePath = os.path.join(dirTarget, file)
                            fileSize = os.path.getsize(filePath)
                            numberOfFilesTargets += 1
                            totalFileSizeTargets += fileSize

                if subdirname == "Concordantie":
                    files = [f for f in os.listdir(thisDirectory) if os.path.isfile(os.path.join(thisDirectory, f))]
                    for file in files:
                        filePath = os.path.join(thisDirectory, file)
                        fileSize = os.path.getsize(filePath)
                        numberOfFilesConcordantie += 1
                        totalFileSizeConcordantie += fileSize

                if subdirname == "Checksums":
                    files = [f for f in os.listdir(thisDirectory) if os.path.isfile(os.path.join(thisDirectory, f))]
                    for file in files:
                        filePath = os.path.join(thisDirectory, file)
                        fileSize = os.path.getsize(filePath)
                        numberOfFilesChecksums += 1
                        totalFileSizeChecksums += fileSize

        # Calculate aggregate stats
        numberOfFiles = numberOfFilesMaster + numberOfFilesAccess + numberOfFilesConcordantie + numberOfFilesTargets + numberOfFilesChecksums
        totalFileSize = totalFileSizeMaster + totalFileSizeAccess + totalFileSizeConcordantie + totalFileSizeTargets + totalFileSizeChecksums
        try:
            averageFileSize = totalFileSize/numberOfFiles
        except ZeroDivisionError:
            pass
        try:
            averageFileSizeMaster = totalFileSizeMaster/numberOfFilesMaster
        except ZeroDivisionError:
            pass
        try:
            averageFileSizeAccess = totalFileSizeAccess/numberOfFilesAccess
        except ZeroDivisionError:
            pass
        try:
            averageFileSizeConcordantie = totalFileSizeConcordantie/numberOfFilesConcordantie
        except ZeroDivisionError:
            pass
        try:
            averageFileSizeTargets = totalFileSizeTargets/numberOfFilesTargets
        except ZeroDivisionError:
            pass
        try:
            averageFileSizeChecksums = totalFileSizeChecksums/numberOfFilesChecksums
        except ZeroDivisionError:
            pass
        # Find input pakbon file based on naming pattern
        foundInputPakbonFile = False
        parsedPakbonIn = False

        dirPakbonIn = os.path.join(self.dirIn, "Pakbon")
        files = [f for f in os.listdir(dirPakbonIn) if os.path.isfile(os.path.join(dirPakbonIn, f))]
        for file in files:
            if "pakbon" in file and file.endswith(".xml"):
                pakbonIn = os.path.join(dirPakbonIn , file)
                foundInputPakbonFile = True

        if foundInputPakbonFile:
            try:
                ns = {'dgmmh': 'http://schemas.kb.nl/dgmmh/v1'}
                # Register namespace, so tag is preserved in output file
                # (from: https://stackoverflow.com/a/54491129/1209004)
                ET.register_namespace('dgmmh', 'http://schemas.kb.nl/dgmmh/v1')
                tree = ET.parse(pakbonIn)
                pbroot = tree.getroot()
                parsedPakbonIn = True
            except Exception:
                logging.error("cannot parse XML in {}".format(pakbonIn))
                self.noErrors += 1
        else:
            logging.error("missing pakbon file in input batch")
            self.noErrors += 1

        if parsedPakbonIn:

            filesElt = pbroot.find("dgmmh:files", ns)
            filesElt.attrib["numberOfFiles"] = str(numberOfFiles)
            filesElt.attrib["totalFileSize"] = str(totalFileSize)
            filesElt.attrib["averageFileSize"] = str(averageFileSize)

            for elt in filesElt:
                if elt.attrib["fileTypeName"] == "master":
                    elt.attrib["numberOfFiles"] = str(numberOfFilesMaster)
                    elt.attrib["totalFileSize"] = str(totalFileSizeMaster)
                    elt.attrib["averageFileSize"] = str(averageFileSizeMaster)
                if elt.attrib["fileTypeName"] == "access":
                    elt.attrib["numberOfFiles"] = str(numberOfFilesAccess)
                    elt.attrib["totalFileSize"] = str(totalFileSizeAccess)
                    elt.attrib["averageFileSize"] = str(averageFileSizeAccess)
                if elt.attrib["fileTypeName"] == "concordantie":
                    elt.attrib["numberOfFiles"] = str(numberOfFilesConcordantie)
                    elt.attrib["totalFileSize"] = str(totalFileSizeConcordantie)
                    elt.attrib["averageFileSize"] = str(averageFileSizeConcordantie)
                if elt.attrib["fileTypeName"] == "targets":
                    elt.attrib["numberOfFiles"] = str(numberOfFilesTargets)
                    elt.attrib["totalFileSize"] = str(totalFileSizeTargets)
                    elt.attrib["averageFileSize"] = str(averageFileSizeTargets)
                if elt.attrib["fileTypeName"] == "checksums":
                    elt.attrib["numberOfFiles"] = str(numberOfFilesChecksums)
                    elt.attrib["totalFileSize"] = str(totalFileSizeChecksums)
                    elt.attrib["averageFileSize"] = str(averageFileSizeChecksums)


            filesElt.attrib["numberOfFiles"] = str(numberOfFilesMaster + numberOfFilesAccess + numberOfFilesConcordantie + numberOfFilesTargets + numberOfFilesChecksums)

            pakbonOut =  os.path.join(self.dirOut, "Pakbon", "pakbon.xml")

            try:
                tree.write(pakbonOut)
            except Exception:
                    logging.error("cannot write XML to {}".format(pakbonOut))
                    self.noErrors += 1
