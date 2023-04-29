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


class appamanScrapper(shopify):
    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(appamanScrapper, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        return spider

    def GetProductUrls(self, homePageResponse):
        # ========== Category And Subcategory ==========#

        topCategoryNodes = homePageResponse.xpath(
            "//ul[contains(@class,'site-navigation')]/li[a[contains(text(),'Boys') or contains(text(),'Girls') or contains(text(),'SALE')  or contains(text(),'NEW')]]")
        for topCategoryNode in topCategoryNodes:
            topCategoryTitle = topCategoryNode.xpath("./a/text()").get().strip()
            topCategorylink = topCategoryNode.xpath("./a/@href").get()
            if not topCategorylink.startswith(store_url):
                topCategorylink = store_url.rstrip('/') + topCategorylink

            topCategoryLinkResponse = requests.get(topCategorylink)
            topCategoryLinkResponse = HtmlResponse(url=topCategorylink, body=topCategoryLinkResponse.text,
                                                   encoding='utf-8')

            categoryNodes = topCategoryLinkResponse.xpath(
                "//div[contains(@class,'drawer__scrollable')]/div/div[contains(button/text(),'Product Type')]/div/div/ul/li/a[contains(text(),'Suit') "
                "or contains(text(),'Dress') or contains(text(),'Jumpsuits') or contains(text(),'Two-piece')]")
            for categoryNode in categoryNodes:
                categoryTitle = categoryNode.xpath("./text()").get().strip()
                categorylink = categoryNode.xpath("./@href").get()
                if not categorylink.startswith(store_url):
                    categorylink = store_url.rstrip('/') + categorylink

                if (topCategoryTitle == "WHAT'S NEW" or topCategoryTitle == "SALE") and (
                        categoryTitle == 'Dresses' or categoryTitle == 'Rompers & Jumpsuits'):
                    category = 'Girl ' + topCategoryTitle + " " + categoryTitle
                elif topCategoryTitle == "SALE" and (
                        categoryTitle == 'Suit Pants' or categoryTitle == 'Mod Suits'):
                    category = 'Boy ' + topCategoryTitle + " " + categoryTitle
                else:
                    category = topCategoryTitle + " " + categoryTitle
                self.listing(categorylink, category)
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

    def GetProducts(self, response):
        ignorProduct = self.IgnoreProduct(response)
        if ignorProduct == True:
            self.ProductIsOutofStock(GetterSetter.ProductUrl)
        shopify.productJson = json.loads(self.SetProductJson(response))
        categoryAndName = shopify.GetCategory(self, response) + " " + self.GetName(response)
        if (re.search("WHAT'S NEW", categoryAndName, re.IGNORECASE) or
            re.search('SALE', categoryAndName, re.IGNORECASE)) and not \
                re.search(r'\b((shirt(dress?)|jump(suit?)|dress|gown|suit|caftan)(s|es)?)\b', categoryAndName,
                          re.IGNORECASE):
            print('Skipping Non Dress Product')
            self.ProductIsOutofStock(GetterSetter.ProductUrl)
        else:
            self.GetProductInfo(response)

    def SetProductJson(self, response):
        print("Invoke product json api for: ", GetterSetter.ProductUrl)
        productJsonStr = requests.get(GetterSetter.ProductUrl + '.js',
                                      cookies=Spider_BaseClass.cookiesDict).content
        return productJsonStr

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

    def IgnoreProduct(self, response):
        if re.search('"availability":', response.text):
            productAvailability = response.text.split('"availability":')[1].split(',')[0].strip()
            if not 'InStock' in productAvailability:
                return True
            else:
                return False
