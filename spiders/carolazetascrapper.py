import json
import re
import sys
from pathlib import Path

DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(DIR.parent.parent.parent.parent))
__package__ = DIR.name

import django

django.setup()
from Shopify import *
from scrapy import signals


store_url = sys.argv[4]


class Carolazetascrapper(shopify):
    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(Carolazetascrapper, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        return spider

    def GetProductUrls(self, homePageResponse):
        # ========== Category And Subcategory ==========#
        topCategoryNodes = homePageResponse.xpath(
            "//nav[contains(@class,'Header__MainNav')]/ul/li[a[text()='Women']]")
        for topCategoryNode in topCategoryNodes:
            topCategoryTitle = topCategoryNode.xpath("./a/text()").get().strip()
            topCategorylink = topCategoryNode.xpath("./a/@href").get()
            if not topCategorylink.startswith(store_url):
                topCategorylink = store_url.rstrip('/') + topCategorylink
            print("TOP CATEGORY  :", topCategoryTitle, "TOP CATEGORY LINK  :", topCategorylink)
            categoryNodes = topCategoryNode.xpath(
                "./div/ul/li/a[contains(text(),'Clothing')]")
            for categoryNode in categoryNodes:
                categoryTitle = categoryNode.xpath("./text()").get().strip()
                categorylink = categoryNode.xpath("./@href").get()
                if not categorylink.startswith(store_url):
                    categorylink = store_url.rstrip('/') + categorylink
                print("CATEGORY  :", categoryTitle)
                if re.search('\?', categorylink):
                    categorylink = 'https' + categorylink.split('https' or 'http')[1].split('?')[0].strip()
                CategoryLinkResponse = requests.get(categorylink)
                CategoryLinkResponse = HtmlResponse(url=categorylink, body=CategoryLinkResponse.text, encoding='utf-8')
                self.listing(CategoryLinkResponse, categoryTitle, store_url)
        return Spider_BaseClass.AllProductUrls

    def listing(self, categoryPageResponse, category, store_url):
        product_list = categoryPageResponse.xpath("//div[contains(@class,'ProductItem__Info ')]/h2/a/@href").extract()
        print("product list : ", product_list)
        for productUrl in product_list:
            if not productUrl.startswith(store_url):
                productUrl = store_url.rstrip('/') + productUrl
            productUrl = self.GetCanonicalUrl(productUrl)
            print('prod url link :', productUrl)
            Spider_BaseClass.AllProductUrls.append(productUrl)
            siteMapCategory = str(Spider_BaseClass.ProductUrlsAndCategory.get(productUrl)).replace('None', '')
            if siteMapCategory:
                Spider_BaseClass.ProductUrlsAndCategory[productUrl] = siteMapCategory + " " + category
            else:
                Spider_BaseClass.ProductUrlsAndCategory[productUrl] = category
        try:
            nextpage = categoryPageResponse.xpath("//link[@rel='next']/@href").extract()[0]
            if not nextpage.startswith(store_url):
                nextpage = store_url.rstrip('/') + nextpage
            print("NEXTPAGE URL :",nextpage)
            nextpageresponse = requests.get(nextpage)
            nextpageresponse = HtmlResponse(url=nextpage, body=nextpageresponse.text, encoding='utf-8')
            self.listing(nextpageresponse, category, store_url)
        except:
            pass

    def GetCategory(self, response):
        filterList = []
        if GetterSetter.ProductUrl in Spider_BaseClass.ProductUrlsAndCategory:
            categories = Spider_BaseClass.ProductUrlsAndCategory[GetterSetter.ProductUrl]
            for category in str(categories).split('$'):
                filterList.append(category)
        for filter in shopify.productJson['tags']:
            filterList.append(filter)
        filters = '$'.join(map(str, filterList)) + '$'
        # print("Product Filters: " + str(filters))
        return filters
