import json
import sys
from pathlib import Path

DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(DIR.parent.parent.parent.parent))
__package__ = DIR.name

import django

django.setup()
from BaseClass import *
from scrapy import signals

store_url = sys.argv[4]


class BurberryScrapper(Spider_BaseClass):
    product_json = ''

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(BurberryScrapper, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        return spider

    def GetProductUrls(self, response):
        category_json = str(response.text).split(',"headerNavigation":')[1].split(',"footerNavigation"')[0]
        category_json = json.loads(category_json)
        for top_category_node in category_json:
            top_category_name = top_category_node['navigationPath']
            list = ['Women', 'Men', 'Children']
            if not Enumerable(list).where(lambda x: x in top_category_name).first_or_default():
                continue
            print('topo_cat_name :', top_category_name)
            category_nodes = top_category_node['items']
            for category_node in category_nodes:
                category_name = category_node['link']['title']
                list2 = ["Clothing", 'Baby 0-24 MTHS', 'Girl 3-14 YRS', 'Boy 3-14 YRS']
                if not Enumerable(list2).where(lambda x: x in category_name).first_or_default():
                    continue
                print("CategoryName :", category_name)
                sub_category_nodes = category_node['items']
                for sub_category_node in sub_category_nodes:
                    sub_category_name = sub_category_node['link']['title']
                    list3 = ['Dresses', 'Knitwear', 'Knitwear & Sweatshirts', 'Dresses & Jumpsuits', 'Midi']
                    if not Enumerable(list3).where(lambda x: x in sub_category_name).first_or_default():
                        continue
                    sub_category_link = sub_category_node['link']['href']
                    if not sub_category_link.startswith(store_url):
                        sub_category_link = store_url.rstrip('/') + sub_category_link
                    print(sub_category_name, " :", sub_category_link)
        return Spider_BaseClass.AllProductUrls
