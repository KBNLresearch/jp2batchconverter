#! /usr/bin/env python3
"""Module for writing summary file"""

import os
import xml.etree.ElementTree as ET
from xml.dom import minidom
import logging


class SummaryFile:
    """SummaryFile class"""

    def __init__(self, summaryFile, summaryDict):

        self.summaryFile = summaryFile
        self.summaryDict = summaryDict
        self.noErrors = 0

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
        for key, value in self.summaryDict.items():
            self.addProperty(root, key, value)

        # Element to string
        xmlOut = ET.tostring(root, 'unicode', 'xml')

        # Make xml pretty
        xmlPretty = minidom.parseString(xmlOut).toprettyxml('    ')

        # Write output
        try:
            with open(self.summaryFile, 'w', newline='', encoding='utf-8') as fSum:
                fSum.write(xmlPretty)
        except Exception:
            logging.error("cannot write summary file to {}".format(self.summaryFile))
            self.noErrors += 1
