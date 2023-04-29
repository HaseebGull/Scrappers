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

class Toddsnyderscrapper(shopify):
    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(Toddsnyderscrapper, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        return spider

    def GetProductUrls(self, homePageResponse):
        # ========== Category And Subcategory ==========#
        topCategoryNodes = homePageResponse.xpath(
            "//div[@class='main_nav_wrapper']/div/div/ul/div[@class='vertical-menu']/li[a[contains(text(),'Suiting')]]")
        for topCategoryNode in topCategoryNodes:
            topCategoryTitle = topCategoryNode.xpath("./a/text()").get().strip()
            topCategorylink = topCategoryNode.xpath("./a/@href").get().strip()
            topCategory_data_dropdown = topCategoryNode.xpath("./a/@data-dropdown-rel").get().strip()
            if not topCategorylink.startswith(store_url):
                topCategorylink = store_url.rstrip('/') + topCategorylink
            categoryNodes = homePageResponse.xpath(
                "//div[@class='main_nav_wrapper']//div[@data-dropdown='" + topCategory_data_dropdown +
                "']//ul/li/a[contains(text(),'Suits') or contains(text(),'Tuxedos') or contains(text(),'Dress Shirts') "
                "or contains(text(),'Suit Pants')]")
            for categoryNode in categoryNodes:
                categoryTitle = categoryNode.xpath("./text()").get().strip()
                categorylink = categoryNode.xpath("./@href").get()
                if not categorylink.startswith(store_url):
                    categorylink = store_url.rstrip('/') + categorylink
                category = "Men " + topCategoryTitle + " " + categoryTitle
                self.listing(categorylink, category)
        return Spider_BaseClass.AllProductUrls

    def listing(self, categorylink, category):
        categoryLinkResponse = requests.get(categorylink)
        categoryLinkResponse = HtmlResponse(url=categorylink, body=categoryLinkResponse.text, encoding='utf-8')
        product_list = categoryLinkResponse.xpath("//div[@class='thumbnail-overlay']/a/@href").extract()
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
            nextPageUrl = categoryLinkResponse.xpath("//link[@rel='next']/@href").extract()[0]
            if not nextPageUrl.startswith(store_url):
                nextPageUrl = store_url.rstrip('/') + nextPageUrl
            self.listing(nextPageUrl, category)
        except:
            pass

    def SetproductJson(self, response):
        if re.search('var product_json = {', response.text):
            ProductJsonStr = '{' + response.text.split('var product_json = {')[1].split('"content"')[
                0].strip().rstrip(
                ',') + '}'
        else:
            print("Invoke product json api for: ", GetterSetter.ProductUrl)
            ProductJsonStr = requests.get(GetterSetter.ProductUrl + '.js',
                                          cookies=Spider_BaseClass.cookies_dict).content

        return ProductJsonStr

    def IgnoreProduct(self, response):
        try:
            preOrder = response.xpath(
                "(//button[contains(@class,'add_to_cart')]/span[contains(text(),'Pre-order')])[1]/text()").get().strip()
            if preOrder:
                return True
        except:
            if re.search('"availability":', response.text):
                productAvailability = response.text.split('"availability":')[1].split(',')[0].strip()
                if not 'InStock' in productAvailability:
                    return True
                else:
                    return False
