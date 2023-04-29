import sys
from pathlib import Path

DIR = Path(__file__).resolve().parent
print('**', DIR.parent.parent.parent.parent.parent)
sys.path.insert(0, str(DIR.parent.parent.parent.parent))
__package__ = DIR.name

from lxml import html
import re
import django
import json

django.setup()
from Magento import magento
from Shopify import shopify
from BaseClass import Spider_BaseClass


class Shopsuggiesscraper(shopify):
    pass
