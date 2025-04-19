#!/usr/bin/env python
# encoding: utf-8

"""
rfidtest.py

Test RFID reader functionality.
"""

import sys
import logging
sys.path.append('..')
from rfid import Reader

logger = logging.getLogger(__name__)

# Remove any existing handlers to prevent duplicate logging
for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)
