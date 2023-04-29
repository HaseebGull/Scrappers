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


class WhiteFoxScrapper(shopify):
    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(WhiteFoxScrapper, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        return spider

    def GetProductUrls(self, homePageResponse):
        # ========== Category And Subcategory ==========#
        topCategoryNodes = homePageResponse.xpath(
            "//div[contains(@class,'nav__dropdown')]/ul/li/a[contains(strong/text(),'New') or contains(strong/text(),'Clothing') or contains(strong/text(),'Sale')]")
        for topCategoryNode in topCategoryNodes:
            topCategoryTitle = topCategoryNode.xpath("./strong/text()").get().strip()
            topCategorylink = topCategoryNode.xpath("./@href").get()
            if not topCategorylink.startswith(store_url):
                topCategorylink = store_url.rstrip('/') + topCategorylink

            categoryNodes = homePageResponse.xpath(
                "//div[@parent-item='" + topCategoryTitle.lower().replace(' ',
                                                                          '-') + "']//ul[contains(@class,'menu flex-grow-1')]/li[a[@class='menu__link' and (contains(span/text(),'Dress') or contains(strong/text(),'Dress') or contains(strong/text(),'Pyjamas'))]]")
            for categoryNode in categoryNodes:
                try:
                    categoryTitle = categoryNode.xpath("./a/strong/text()").get().strip()
                except:
                    categoryTitle = categoryNode.xpath("./a/span/text()").get().strip()
                categorylink = categoryNode.xpath("./a/@href").get()
                if not categorylink.startswith(store_url):
                    categorylink = store_url.rstrip('/') + categorylink

                subCategoryNodes = categoryNode.xpath(
                    "./following-sibling::ul/li[@class='menu__item']/a[not(contains(span/text(),'All'))]")
                if not subCategoryNodes:
                    category = 'Women ' + topCategoryTitle + " " + categoryTitle
                    self.listing(categorylink, category)
                else:
                    for subCategoryNode in subCategoryNodes:
                        subCategoryTitle = subCategoryNode.xpath("./span/text()").get().strip()
                        subCategorylink = subCategoryNode.xpath("./@href").get()
                        if not subCategorylink.startswith(store_url):
                            subCategorylink = store_url.rstrip('/') + subCategorylink

                        # =================== BREADCRUM =================== #
                        category = 'Women ' + topCategoryTitle + " " + categoryTitle + " " + subCategoryTitle
                        # ======================================#
                        self.listing(categorylink, category)
        return Spider_BaseClass.AllProductUrls

    def listing(self, categorylink, category):
        CategoryLinkResponse = requests.get(categorylink)
        categoryPageResponse = HtmlResponse(url=categorylink, body=CategoryLinkResponse.text, encoding='utf-8')
        product_list = categoryPageResponse.xpath(
            "//a[@class='bc-sf-filter-product-item-title']/@href").extract()
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

    def IgnoreProduct(self, response):
        productAvailability = response.xpath("//meta[@property='product:availability']/@content").get().strip()
        if not 'instock' in productAvailability:
            return True
        else:
            return False
