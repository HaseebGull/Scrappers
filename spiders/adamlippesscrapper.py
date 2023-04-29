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


class AdamlippesScrapper(shopify):
    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(AdamlippesScrapper, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        return spider

    def GetProductUrls(self, homePageResponse):
        # ========== Category And Subcategory ==========#
        topCategoryNodes = homePageResponse.xpath(
            "//nav[contains(@class,'Header__MainNav')]/ul/li[a[contains(text(),'WOMEN') or contains(text(),'SALE') or contains(text(),'ICONS') or contains(text(),'FEATURED')]]")
        for topCategoryNode in topCategoryNodes:
            topCategoryTitle = topCategoryNode.xpath("./a/text()").get().strip()
            topCategorylink = topCategoryNode.xpath("./a/@href").get()
            if not topCategorylink.startswith(store_url):
                topCategorylink = store_url.rstrip('/') + topCategorylink
            categoryNodes = topCategoryNode.xpath(
                ".//ul[contains(@class,'MegaMenu__Item') or contains(@class,'Linklist')]/li/a[contains(text(),'Dress') or contains(text(),'Jumpsuits') or contains(text(),'New')]")
            for categoryNode in categoryNodes:
                categoryTitle = categoryNode.xpath("./text()").get().strip()
                categorylink = categoryNode.xpath("./@href").get()
                if not categorylink.startswith(store_url):
                    categorylink = store_url.rstrip('/') + categorylink
                if re.search('\?', categorylink):
                    categorylink = 'https' + categorylink.split('https' or 'http')[1].split('?')[0].strip()

                # =================== BREADCRUM ===================3
                category = topCategoryTitle + " " + categoryTitle
                # ======================================#
                self.listing(categorylink, category)
        return Spider_BaseClass.AllProductUrls

    def listing(self, categorylink, category):
        CategoryLinkResponse = requests.get(categorylink)
        categoryPageResponse = HtmlResponse(url=categorylink, body=CategoryLinkResponse.text, encoding='utf-8')
        product_list = categoryPageResponse.xpath(
            "//section[contains(@class,'plp-grid-item-wrapper row')]/div/div/div/figure/a/@href").extract()
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
                categoryPageResponse.xpath("//ul[@class='pagination']/li/a[contains(text(),'Next')]/@href").extract()[0]
            if not nextpageUrl.startswith(store_url):
                nextpageUrl = store_url.rstrip('/') + nextpageUrl
            self.listing(nextpageUrl, category)
        except:
            pass

    def GetProducts(self, response):
        ignorProduct = self.IgnoreProduct(response)
        if ignorProduct == True:
            self.ProductIsOutofStock(GetterSetter.ProductUrl)
        else:
            shopify.productJson = json.loads(self.SetProductJson(response))
            categoryAndName = shopify.GetCategory(self, response) + " " + self.GetName(response)
            if (re.search('sale', categoryAndName, re.IGNORECASE) or
                re.search('new arrival', categoryAndName, re.IGNORECASE)) and not \
                    re.search(r'\b((shirt(dress?)|jump(suit?)|dress|gown|suit|caftan)(s|es)?)\b', categoryAndName,
                              re.IGNORECASE):
                print('Skipping Non Dress Product')
                self.ProductIsOutofStock(GetterSetter.ProductUrl)
            else:
                self.GetProductInfo(response)

    def GetName(self, response):
        color = self.GetSelectedColor(response)
        name = shopify.GetName(self, response)
        if not color == '' and not re.search(color, name):
            name = name + ' - ' + color
        return name

    def GetSelectedColor(self, response):
        return response.xpath(
            "//div[@class='ProductForm__Swatch-label' and contains(span/text(),'COLOR')]/span[contains(@class,'Swatch-label__title')]/text()").get().strip()

    def IgnoreProduct(self, response):
        if re.search('"availability":', response.text):
            productAvailability = response.text.split('"availability":')[1].split(',')[0].strip()
            if not 'InStock' in productAvailability:
                return True
            else:
                return False
