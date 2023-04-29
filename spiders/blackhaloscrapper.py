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


class Blackhaloscrapper(shopify):
    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(Blackhaloscrapper, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        return spider

    def GetProductUrls(self, homePageResponse):
        # ========== Category And Subcategory ==========#
        global gender
        gender = 'Women '  # Found Only Women Products
        topCategoryNodes = homePageResponse.xpath(
            "//nav[contains(@class,'desktop__nav-menu-items')]/div[a[contains(text(),'Shop') or contains(text(),'Sale') or contains(text(),'New')]]")
        for topCategoryNode in topCategoryNodes:
            topCategoryTitle = topCategoryNode.xpath("./a/text()").get().strip()
            topCategorylink = topCategoryNode.xpath("./a/@href").get()
            if not topCategorylink.startswith(store_url):
                topCategorylink = store_url.rstrip('/') + topCategorylink

            categoryNodes = topCategoryNode.xpath(
                ".//div[contains(@class,'meganav__nav-link js-nav__link')][a[text()='Dresses' or text()='Jumpsuits' or text()='Two Piece Dressing' or text()='Minis']]")
            if not categoryNodes:
                category = gender + topCategoryTitle
                self.listing(topCategorylink, category)
            for categoryNode in categoryNodes:
                categoryTitle = categoryNode.xpath("./a/text()").get().strip()
                categorylink = categoryNode.xpath("./a/@href").get()
                if not categorylink.startswith(store_url):
                    categorylink = store_url.rstrip('/') + categorylink
                if re.search('\?', categorylink):
                    categorylink = 'https' + categorylink.split('https' or 'http')[1].split('?')[0].strip()
                # ==================================== BREADCRUM ================================= #
                category = gender + topCategoryTitle + " " + categoryTitle
                self.listing(categorylink, category)
        return Spider_BaseClass.AllProductUrls

    def listing(self, categorylink, category):
        CategoryLinkResponse = requests.get(categorylink)
        CategoryLinkResponse = HtmlResponse(url=categorylink, body=CategoryLinkResponse.text,
                                            encoding='utf-8')

        apiUrl = categorylink + '?view=json&page=1'
        responeapi = requests.get(url=apiUrl, timeout=6000)
        apiresponse = json.loads(responeapi.content)
        self.GetUrls(apiresponse, category)
        nextPageUrl = apiresponse['url']
        while nextPageUrl != '':
            if not nextPageUrl.startswith(store_url):
                nextPageUrl = store_url.rstrip('/') + apiresponse['url']
            responeapi = requests.get(url=nextPageUrl, timeout=6000)
            apiresponse = json.loads(responeapi.content)
            nextPageUrl = apiresponse['url']
            self.GetUrls(apiresponse, category)

    def GetUrls(self, dataJson, category):
        for apiproduct in dataJson['products']:
            apiproducturl = store_url.rstrip('/') + apiproduct['url']
            productUrl = self.GetCanonicalUrl(apiproducturl)
            Spider_BaseClass.AllProductUrls.append(productUrl)
            siteMapCategory = str(Spider_BaseClass.ProductUrlsAndCategory.get(productUrl)).replace('None', '')
            if siteMapCategory:
                Spider_BaseClass.ProductUrlsAndCategory[productUrl] = siteMapCategory + " " + category
            else:
                Spider_BaseClass.ProductUrlsAndCategory[productUrl] = category

    def GetProducts(self, response):
        ignorProduct = self.IgnoreProduct(response)
        if ignorProduct == True:
            self.ProductIsOutofStock(GetterSetter.ProductUrl)
        shopify.productJson = json.loads(self.SetProductJson(response))
        categoryAndName = shopify.GetCategory(self, response) + " " + self.GetName(response)
        if (re.search('sale', categoryAndName, re.IGNORECASE) or re.search('new arrival', categoryAndName,
                                                                           re.IGNORECASE)) and not re.search(
            r'\b((shirt(dress?)|jump(suit?)|dress|gown|suit|caftan)(s|es)?)\b', categoryAndName, re.IGNORECASE):
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

    def GetDescription(self, response):
        baseDesc = shopify.GetDescription(self, response)
        description = response.xpath(
            "//div[@id='product-here']//div[contains(@class,'details-body')]/ul[contains(@class,'product-details-ul') or contains(@class,'product-fabrication-ul')]/li/text()").extract()
        description = ' '.join(map(str, description))
        return baseDesc + " " + description
