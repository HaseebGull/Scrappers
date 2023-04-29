import sys
from pathlib import Path
from Magento import *
DIR = Path(__file__).resolve().parent
print('**', DIR.parent.parent.parent.parent.parent)
sys.path.insert(0, str(DIR.parent.parent.parent.parent))
__package__ = DIR.name
import django
django.setup()

class AlanahillScraper(magento):
    print('Hill')




