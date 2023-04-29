import sys
from pathlib import Path

DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(DIR.parent.parent.parent.parent))
__package__ = DIR.name

import django

django.setup()
from Shopify import *
from BaseClass import Spider_BaseClass
from scrapy import signals

store_url = sys.argv[4]


class Wildfoxscrapper(shopify):
    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(Wildfoxscrapper, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        return spider

    def GetProductUrls(self, homePageResponse):
        # ========== Category And Subcategory ==========#
        topCategoryNodes = homePageResponse.xpath(
            "//nav[@class='nav-bar']/ul/li[a[contains(text(),'Shop') or contains(text(),'Sale')]]")
        for topCategoryNode in topCategoryNodes:
            topCategoryTitle = topCategoryNode.xpath("./a/text()").get().strip()
            topCategorylink = topCategoryNode.xpath("./a/@href").get()
            categoryNodes = topCategoryNode.xpath(
                "./ul/li[a[contains(text(),'Clothing') or contains(text(),'All Sale')]]")
            for categoryNode in categoryNodes:
                categoryTitle = categoryNode.xpath("./a/text()").get().strip()
                categorylink = categoryNode.xpath("./a/@href").get()
                subCategoryNodes = categoryNode.xpath(
                    "./ul/li/a[contains(text(),'Dresses')]")
                for subCategoryNode in subCategoryNodes:
                    subCategoryTitle = subCategoryNode.xpath("./text()").get().strip()
                    subCategorylink = subCategoryNode.xpath("./@href").get()
                    if not subCategorylink.startswith(store_url):
                        subCategorylink = store_url.rstrip('/') + subCategorylink
                    category = "Women " + topCategoryTitle + " " + categoryTitle + " " + subCategoryTitle
                    self.listing(subCategorylink, category)

        return Spider_BaseClass.AllProductUrls

    def listing(self, categorylink, category):
        categoryLinkResponse = requests.get(categorylink)
        categoryLinkResponse = HtmlResponse(url=categorylink, body=categoryLinkResponse.text, encoding='utf-8')
        product_list = categoryLinkResponse.xpath("//figcaption/div[@class='product-title']/a/@href").extract()
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
            nextPageUrl = categoryLinkResponse.xpath("//link[@rel='next']/@href").get()
            if not nextPageUrl.startswith(store_url):
                nextPageUrl = store_url.rstrip('/') + nextPageUrl
            self.listing(nextPageUrl, category)
        except:
            pass

    def IgnoreProduct(self, response):
        if re.search('"availability":', response.text):
            productAvailability = response.text.split('"availability":')[1].split(',')[0].strip()
            if not 'InStock' in productAvailability:
                return True
            else:
                return False
