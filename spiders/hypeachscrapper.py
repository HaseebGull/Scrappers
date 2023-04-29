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

Spider_BaseClass.testingGender = 'Women'


class HypeachScrapper(shopify):
    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(HypeachScrapper, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        return spider

    shopify.optPropObj.ignoreOptionNames.extend(['Material'])

    def GetProductUrls(self, homePageResponse):
        # ========== Category And Subcategory ==========#
        topCategoryNodes = homePageResponse.xpath(
            "//div[@class='h-sec-menu__wrapper']/ul/li[a[contains(text(),'New') or contains(text(),'Clothing') or contains(text(),'dress') or contains(text(),'Sale')]]")
        for topCategoryNode in topCategoryNodes:
            topCategoryTitle = topCategoryNode.xpath("./a/text()").get().strip()
            topCategorylink = topCategoryNode.xpath("./a/@href").get()
            if not topCategorylink.startswith(store_url):
                topCategorylink = store_url.rstrip('/') + topCategorylink
            categoryNodes = topCategoryNode.xpath(
                "./ul/li/a[not(contains(text(),'Shop')) and not(contains(text(),'Outerwear')) and not(contains(text(),'Denim')) and not(contains(text(),'Bottoms')) and not(contains(text(),'Tops'))]")
            if not categoryNodes:
                category = 'Women ' + topCategoryTitle
                self.listing(topCategorylink, category)
            for categoryNode in categoryNodes:
                categoryTitle = categoryNode.xpath("./text()").get().strip()
                categorylink = categoryNode.xpath("./@href").get()
                if not categorylink.startswith(store_url):
                    categorylink = store_url.rstrip('/') + categorylink
                if re.search('\?', categorylink):
                    categorylink = 'https' + categorylink.split('https' or 'http')[1].split('?')[0].strip()

                # =================== BREADCRUM ===================3
                category = 'Women ' + topCategoryTitle + " " + categoryTitle
                # ======================================#
                self.listing(categorylink, category)
        return Spider_BaseClass.AllProductUrls

    def listing(self, categorylink, category):
        CategoryLinkResponse = requests.get(categorylink)
        categoryPageResponse = HtmlResponse(url=categorylink, body=CategoryLinkResponse.text, encoding='utf-8')
        product_list = categoryPageResponse.xpath(
            "//a[contains(@class,'product-info__caption')]/@href").extract()
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
                categoryPageResponse.xpath("//link[@rel='next']/@href").extract()[0]
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
        if (re.search(r'\b' + 'New' + r'\b', categoryAndName, re.IGNORECASE) or
            re.search(r'\b' + 'Sale' + r'\b', categoryAndName, re.IGNORECASE)) and not \
                re.search(r'\b((shirt(dress?)|jump(suit?)|dress|gown|suit|caftan)(s|es)?)\b', categoryAndName,
                          re.IGNORECASE):
            print('Skipping Non Dress Product')
            self.ProductIsOutofStock(GetterSetter.ProductUrl)
        else:
            self.GetProductInfo(response)

    #
    # def GetName(self, response):
    #     color = self.GetSelectedColor(response)
    #     name = shopify.GetName(self, response)
    #     if not color == '' and not re.search(color, name):
    #         name = name + ' - ' + color
    #     return name
    #
    # def GetSelectedColor(self, response):
    #     return response.xpath(
    #         "//div[@class='ProductForm__Swatch-label' and contains(span/text(),'COLOR')]/span[contains(@class,'Swatch-label__title')]/text()").get().strip()

    def IgnoreProduct(self, response):
        if re.search('"availability":', response.text):
            productAvailability = response.text.split('"availability":')[1].split(',')[0].strip()
            if not 'InStock' in productAvailability:
                return True
            else:
                return False
