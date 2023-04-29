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

class FootasylumScrapper(Spider_BaseClass):
    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(FootasylumScrapper, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        return spider

    def GetProductUrls(self, response):
        # ========== Category And Subcategory ==========#
        topCategoryNodes = response.xpath(
            "(//div[@id='nav0']/div[a[contains(text(),'Landed') or contains(text(),'Men') or contains(text(),"
            "'Wome') or contains(text(),'Kids')]])[1]")
        for top_category_node in topCategoryNodes:
            top_category_title = top_category_node.xpath("./a/text()").get().strip()
            top_category_link = top_category_node.xpath("./a/@href").get()
            if not top_category_link.startswith(store_url):
                top_category_link = store_url.rstrip('/') + top_category_link
            print("TOP CATEGORY  :", top_category_title)
            category_nodes = top_category_node.xpath(
                "(.//div[@class='navcolumn'][div/a[contains(text(),'New') or contains(text(),'Clothing') and not(contains(text(),'Junior'))]])[1]")
            for category_node in category_nodes:
                category_title = category_node.xpath("./div/a/text()").get().strip()
                category_link = category_node.xpath("./div/a/@href").get()
                if not category_link.startswith(store_url):
                    category_link = store_url.rstrip('/') + category_link
                print("CATEGORY  :", category_title)
                sub_category_nodes = category_node.xpath(
                    "(./a[not(contains(text(),'All')) and contains(text(),'Clothing') or contains(text(),'Tracksuits') or contains(text(),'Dresses') or contains(text(),'Loungewear')]")
                for sub_category_node in sub_category_nodes:
                    sub_category_title = sub_category_node.xpath("./text()").get().strip()
                    sub_category_link = sub_category_node.xpath("./@href").get()
                    if not sub_category_link.startswith(store_url):
                        sub_category_link = store_url.rstrip('/') + sub_category_link
                    if "Men" in top_category_link or "Loungewear" in sub_category_title:
                        continue
                    category = top_category_title + " " + category_title + " " + sub_category_title
                    self.listing(sub_category_link, category)
        return Spider_BaseClass.AllProductUrls
    def listing(self, subCategorylink, category):
        subCategoryLinkResponse = requests.get(subCategorylink)
        subCategoryLinkResponse = HtmlResponse(url=subCategorylink, body=subCategoryLinkResponse.text,
                                               encoding='utf-8')
        product_list = subCategoryLinkResponse.xpath(
            "//a[contains(@class,'listing-text')]/@href").extract()
        for productUrl in product_list:
            if not productUrl.startswith(store_url):
                productUrl = store_url.rstrip('/') + productUrl
            print('PRODUCT URL :', productUrl)
            Spider_BaseClass.AllProductUrls.append(productUrl)
            siteMapCategory = str(Spider_BaseClass.ProductUrlsAndCategory.get(productUrl)).replace('None', '')
            if siteMapCategory:
                Spider_BaseClass.ProductUrlsAndCategory[productUrl] = siteMapCategory + " " + category
            else:
                Spider_BaseClass.ProductUrlsAndCategory[productUrl] = category
        try:
            nextPageUrl = subCategoryLinkResponse.xpath("//a[@rel='next']/@href").get()
            if not nextPageUrl.startswith(store_url):
                nextPageUrl = store_url.rstrip('/') + nextPageUrl
                print("NEXT PAGE :", nextPageUrl)
            self.listing(nextPageUrl, category)
        except:
            pass