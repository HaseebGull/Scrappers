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


class AndyandEvanScrapper(shopify):
    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(AndyandEvanScrapper, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        return spider

    def GetProductUrls(self, homePageResponse):
        # ========== Category And Subcategory ==========#

        topCategoryNodes = homePageResponse.xpath(
            "//ul[@class='nav site-nav']/li[a[contains(text(),'Baby') or contains(text(),'Girl') or contains(text(),'Boy') or contains(text(),'New') or contains(text(),'Sale')]]")
        for topCategoryNode in topCategoryNodes:
            topCategoryTitle = topCategoryNode.xpath("./a/text()").get().strip()
            topCategoryLink = topCategoryNode.xpath("./a/@href").get().strip()
            if not topCategoryLink.startswith(store_url):
                topCategoryLink = store_url.rstrip('/') + topCategoryLink
            categoryNodes = topCategoryNode.xpath(
                ".//ul[contains(@class,'dropdown__containe')]/li[a[contains(text(),'Baby Boy (0-24M)') or contains(text(),'Baby Girl (0-24M)') or contains(text(),'Suits') or contains(text(),'Dress')]]")
            if not categoryNodes:
                category = topCategoryTitle
                self.listing(topCategoryLink,category)
            else:
                for categoryNode in categoryNodes:
                    categoryTitle = categoryNode.xpath("./a/text()").get().strip()
                    categorylink = categoryNode.xpath("./a/@href").get()
                    if not categorylink.startswith(store_url):
                        categorylink = store_url.rstrip('/') + categorylink
                    subCategoryNodes = categoryNode.xpath(
                        "./div/ul/li/a[contains(text(),'One-Pieces') or contains(text(),'Suits')  or contains(text(),'Dress') or contains(text(),'Sets')]")
                    for subCategoryNode in subCategoryNodes:
                        subCategoryTitle = subCategoryNode.xpath("./text()").get().strip()
                        subCategorylink = subCategoryNode.xpath("./@href").get()
                        if not subCategorylink.startswith(store_url):
                            subCategorylink = store_url.rstrip('/') + subCategorylink
                        category = topCategoryTitle + " " + categoryTitle + " " + subCategoryTitle
                        self.listing(subCategorylink, category)
        return Spider_BaseClass.AllProductUrls

    def listing(self, categorylink, category):
        CategoryLinkResponse = requests.get(categorylink)
        categoryPageResponse = HtmlResponse(url=categorylink, body=CategoryLinkResponse.text, encoding='utf-8')
        product_list = categoryPageResponse.xpath("//a[contains(@class,'product-item-title')]/@href").extract()
        for productUrl in product_list:
            if not productUrl.startswith(store_url):
                productUrl = store_url.rstrip('/') + productUrl
            productUrl = str(self.GetCanonicalUrl(productUrl)).rstrip('#')
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
        if (re.search('New Arrivals', categoryAndName, re.IGNORECASE) or
            re.search('Sale', categoryAndName, re.IGNORECASE) or
            re.search('Blazers, & Vests', categoryAndName, re.IGNORECASE)) and not \
                re.search(r'\b((shirt(dress?)|jump(suit?)|dress|gown|set|suit|caftan)(s|es)?)\b', categoryAndName,
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
