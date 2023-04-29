import sys
from pathlib import Path

DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(DIR.parent.parent.parent.parent))
__package__ = DIR.name

import django

django.setup()
from scrapy import signals
from Shopify import *

store_url = sys.argv[4]


class AshmiandCoScrapper(shopify):
    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(AshmiandCoScrapper, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        return spider

    def GetProductUrls(self, homePageResponse):
        # ========== Category And Subcategory ==========#

        topCategoryNodes = homePageResponse.xpath(
            "//ul[@class='mobile-nav']/li/a[contains(text(),'Girl') or contains(text(),'Boy') or contains(text(),'Unisex') or contains(text(),'Clearance')]")
        for topCategoryNode in topCategoryNodes:
            topCategoryTitle = topCategoryNode.xpath("./text()").get().strip()
            topCategorylink = topCategoryNode.xpath("./@href").get()
            if not topCategorylink.startswith(store_url):
                topCategorylink = store_url.rstrip('/') + topCategorylink
            if 'Unisex' in topCategoryTitle:
                category = 'Baby Girl Baby Boy ' + topCategoryTitle
            else:
                category = topCategoryTitle
            self.listing(topCategorylink, category)
        return Spider_BaseClass.AllProductUrls

    def listing(self, categorylink, category):
        CategoryLinkResponse = requests.get(categorylink)
        categoryPageResponse = HtmlResponse(url=categorylink, body=CategoryLinkResponse.text, encoding='utf-8')
        product_list = categoryPageResponse.xpath("//div[contains(@class,'product__content')]/a/@href").extract()
        for productUrl in product_list:
            if not productUrl.startswith(store_url):
                productUrl = store_url.rstrip('/') + productUrl
            productUrl = self.GetCanonicalUrl(productUrl)
            Spider_BaseClass.AllProductUrls.append(productUrl)
            siteMapCategory = str(Spider_BaseClass.ProductUrlsAndCategory.get(productUrl)).replace('None', '')
            if siteMapCategory:
                Spider_BaseClass.ProductUrlsAndCategory[productUrl] = siteMapCategory + " " + category
            else:
                Spider_BaseClass.ProductUrlsAndCategory[productUrl] = category
        try:
            nextpageUrl = \
                categoryPageResponse.xpath("//link[@rel='next']/@href").get()
            if not nextpageUrl.startswith(store_url):
                nextpageUrl = store_url.rstrip('/') + nextpageUrl
            self.listing(nextpageUrl, category)
        except:
            pass

    # def GetName(self, response):
    #     color = self.GetSelectedColor(response)
    #     name = response.xpath("//h1[contains(@class,'product-name')]/text()").get().strip()
    #     if not color == '' and not re.search(color, name):
    #         name = name + ' - ' + color
    #     return name
    #
    # def GetSelectedColor(self, response):
    #     try:
    #         color = str(
    #             response.xpath(
    #                 "//div[@class='value color']//li[contains(@class,'selectable selected')]/a/@title").get().strip()).replace(
    #             'Select Color:', '').title().strip()
    #     except:
    #         color = ''
    #     return color
    def GetProducts(self, response):
        ignorProduct = self.IgnoreProduct(response)
        if ignorProduct == True:
            self.ProductIsOutofStock(GetterSetter.ProductUrl)
        shopify.productJson = json.loads(self.SetProductJson(response))
        categoryAndName = shopify.GetCategory(self, response) + " " + self.GetName(response)
        if (re.search('Clearance', categoryAndName, re.IGNORECASE) or
            re.search('Clothing', categoryAndName, re.IGNORECASE)) and not \
                re.search(r'\b((shirt(dress?)|jump(suit?)|dress|romper|gown|overall|suit|caftan)(s|es)?)\b', categoryAndName,
                          re.IGNORECASE):
            print('Skipping Non Dress Product')
            self.ProductIsOutofStock(GetterSetter.ProductUrl)
        else:
            self.GetProductInfo(response)
    def IgnoreProduct(self, response):
        if re.search('"availability":', response.text):
            productAvailability = response.text.split('"availability":')[1].split(',')[0].strip()
            if not 'InStock' in productAvailability:
                return True
            else:
                return False
