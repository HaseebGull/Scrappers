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


class LuisaviaromaScrapper(Spider_BaseClass):
    # Spider_BaseClass.hasDriver = True
    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(LuisaviaromaScrapper, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        return spider

    def GetProductUrls(self, response):
        # response = SeleniumResponse(response)
        top_category_nodes = response.xpath("//ul[@data-id='LVR-menu']/li/a[contains(text(),'Women') or contains(text("
                                            "),'Men') or contains(text(),'Kids')]")
        for top_category_node in top_category_nodes:
            top_category_title = top_category_node.xpath("./text()").get().strip()
            top_category_link = top_category_node.xpath("./@href").get()
            if not top_category_link.startswith(store_url):
                top_category_link = store_url + top_category_link
            print("TOP CATEGORY  :", top_category_title)
            print(top_category_link, " :", top_category_link)
        return Spider_BaseClass.AllProductUrls
