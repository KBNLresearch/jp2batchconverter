#! /usr/bin/env python3
"""Module for writing summary file"""

import os
import xml.etree.ElementTree as ET
from xml.dom import minidom
import logging

class SummaryFile:
    """SummaryFile class"""

    def __init__(self, summaryFile, kbiwVersion, grokVersion, noErrors, noWarnings):


        self.summaryFile = summaryFile
        self.kbiwVersion = kbiwVersion
        self.grokVersion = grokVersion
        self.noErrors = noErrors
        self.noWarnings = noWarnings


    def addProperty(self, element, tag, text):
        """Append childnode with text to Element"""

        el = ET.SubElement(element, tag)
        el.text = str(text)


    def writeSummaryFile(self):
        """Write summary file """

        # Name space and XSD schema strings
        nsString = 'http://kb.nl/ns/kbiw/v1/'
        xsiNsString = 'http://www.w3.org/2001/XMLSchema-instance'

        # Create root element
        root = ET.Element("kbiw", {'xmlns': nsString,
                                    'xmlns:xsi': xsiNsString})

        # Add child elements
        self.addProperty(root, "kbiwVersion", self.kbiwVersion)
        self.addProperty(root, "grokVersion", self.grokVersion)
        self.addProperty(root, "noErrors", self.noErrors)
        self.addProperty(root, "noWarnings", self.noWarnings)
        self.addProperty(root, "comment", "See batch manifest and log file for details on errors and warnings")

        # Element to string
        xmlOut = ET.tostring(root, 'unicode', 'xml')

        # Make xml pretty
        xmlPretty = minidom.parseString(xmlOut).toprettyxml('    ')

        # Set noErrors to 0, in order to get meaningful output in case writing fails
        # (this is a bit confusing as this variable is used for 2 different things here)
        self.noErrors = 0

        # Write output
        try:
            with open(self.summaryFile, 'w', newline='', encoding='utf-8') as fSum:
                fSum.write(xmlPretty)
        except Exception:
                logging.error("cannot write summary file to {}".format(self.summaryFile))
                self.noErrors += 1

