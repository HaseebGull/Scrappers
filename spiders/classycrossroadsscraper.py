print('in alanahill file')

import sys
from pathlib import Path

DIR = Path(__file__).resolve().parent
print('**', DIR.parent.parent.parent.parent.parent)
sys.path.insert(0, str(DIR.parent.parent.parent.parent))
__package__ = DIR.name
import  re
import django
import json
django.setup()
from Magento import magento
from BaseClass import Spider_BaseClass


class Classycrossroadsscraper(magento):

    def GetBrand(self):
        pass

    def GetDescription(self):
        description = Spider_BaseClass.ProductPage.xpath("//div[@class='description data-div']/div/h2/text()")[0]
        # com = re.compile('<.*?>')
        # txt = re.sub(com, '', description).strip()
        return description

    def GetImageUrl(self):
        imageUrl = ''
        if Spider_BaseClass.ProductPage.xpath("//img[@data-zoom-image]//@data-zoom-image"):
            imageUrl = Spider_BaseClass.ProductPage.xpath("//img[@data-zoom-image]//@data-zoom-image")[0]
        elif Spider_BaseClass.ProductPage.xpath("//meta[@property='og:image']/@content"):
            imageUrl = Spider_BaseClass.ProductPage.xpath("//meta[@property='og:image']/@content")
        return imageUrl



