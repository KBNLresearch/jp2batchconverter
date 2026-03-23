#! /usr/bin/env python3
#
"""CLI wrapper script, ensures that relative imports work correctly in a PyInstaller build"""

from jp2batchconverter.jp2batchconverter import main

if __name__ == '__main__':
    main()
