#! /usr/bin/env python3
"""Module for writing summary file"""

import os
import xml.etree.ElementTree as ET
import logging

class SummaryFile:
    """SummaryFile class"""

    def __init__(self, summaryFile, kbiwVersion, grokVersion, noErrors, noWarnings):


        self.summaryFile = summaryFile
        self.kbiwVersion = kbiwVersion
        self.grokVersion = grokVersion
        self.noErrors = noErrors
        self.noWarnings = noWarnings

    def writeSummaryFile(self):
        """Write summary file """

        with open(self.summaryFile, 'w', newline='', encoding='utf-8') as fSum:
            fSum.write("Kbiw version: {}\n".format(self.kbiwVersion))
            fSum.write("Grok version: {}\n".format(self.grokVersion))
            fSum.write("Errors: {}\n".format(self.noErrors))
            fSum.write("Warnings: {}\n".format(self.noWarnings))
            fSum.write(
                "See batch manifest and log file for details on errors and warnings\n")
