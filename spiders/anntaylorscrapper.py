import sys
from pathlib import Path

DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(DIR.parent.parent.parent.parent))
__package__ = DIR.name

import django

django.setup()
from BaseClass import *
from scrapy import signals

store_url = sys.argv[4]


class AnntaylorScrapper(Spider_BaseClass):
    Spider_BaseClass.cookiesDict = {"_IntlCtr": "US", "_IntlCur": "USD"}

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(AnntaylorScrapper, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        return spider

    def GetProductUrls(self, homePageResponse):
        # ========== Category And Subcategory ==========#
        topCategoryNodes = homePageResponse.xpath(
            "//nav/div/div[contains(@class,'sub-nav-wrapper')][a[contains(strong/text(),'Clothing')  or contains(strong/text(),'Petites') or contains(strong/text(),'Sale')]]")
        for topCategoryNode in topCategoryNodes:
            topCategoryTitle = topCategoryNode.xpath("./a/strong/text()").get().strip()
            topCategorylink = topCategoryNode.xpath("./a/@href").get().strip()
            print("TOpTitle :", topCategorylink)
            if not topCategorylink.startswith(store_url):
                topCategorylink = store_url.rstrip('/') + topCategorylink
            topCategoryLinkResponse = requests.get(topCategorylink)
            topCategoryLinkResponse = HtmlResponse(url=topCategorylink, body=topCategoryLinkResponse.text,
                                                   encoding='utf-8')
            categoryNodes = topCategoryLinkResponse.xpath(
                "(//div[@data-component='LeftNavigation']/a[contains(text(),'Clothing') or contains(text(),'Sale') or contains(text(),'Petites')])[1]")
            for categoryNode in categoryNodes:
                categoryTitle = categoryNode.xpath("./text()").get().strip()
                print("CatTitle :", categoryTitle)
                if categoryNode.xpath(
                        "./following-sibling::nav/a[contains(text(),'Dress') or contains(text(),'Sleep')]"):
                    subCategoryNodes = categoryNode.xpath(
                        "./following-sibling::nav/a[contains(text(),'Dress') or contains(text(),'Sleep')]")
                    for subCategoryNode in subCategoryNodes:
                        subCategoryTitle = subCategoryNode.xpath("./text()").get().strip()
                        subCategorylink = subCategoryNode.xpath("./@href").get().strip()
                        if not subCategorylink.startswith(store_url):
                            subCategorylink = store_url.rstrip('/') + subCategorylink
                        category = "Women " + topCategoryTitle + " " + categoryTitle + " " + subCategoryTitle
                        self.listing(subCategorylink, category)
                if categoryNode.xpath(
                        "(./following-sibling::nav/div/a[contains(text(),'Dress') or contains(text(),'Suits')]/following-sibling::nav/a[contains(text(),'Dress')])[1]"):
                    subCategoryNodes = categoryNode.xpath(
                        "(./following-sibling::nav/div/a[contains(text(),'Dress') or contains(text(),'Suits')]/following-sibling::nav/a[contains(text(),'Dress')])[1]")
                    for subCategoryNode in subCategoryNodes:
                        subCategoryTitle = subCategoryNode.xpath("./text()").get().strip()
                        subCategorylink = subCategoryNode.xpath("./@href").get().strip()
                        if not subCategorylink.startswith(store_url):
                            subCategorylink = store_url.rstrip('/') + subCategorylink
                        category = "Women " + topCategoryTitle + " " + categoryTitle + " " + subCategoryTitle
                        self.listing(subCategorylink, category)
        return Spider_BaseClass.AllProductUrls

    def listing(self, categorylink, category):
        categoryLinkResponse = requests.get(categorylink)
        categoryLinkResponse = HtmlResponse(url=categorylink, body=categoryLinkResponse.text, encoding='utf-8')
        product_list = categoryLinkResponse.xpath(
            "(//ul/li/div[@class='product-wrap']/div/a/@href)[1]").extract()
        for productUrl in product_list:
            if 'dress' in productUrl:
                if not productUrl.startswith(store_url):
                    productUrl = store_url.rstrip('/') + productUrl
                Spider_BaseClass.AllProductUrls.append(productUrl)
                siteMapCategory = str(Spider_BaseClass.ProductUrlsAndCategory.get(productUrl)).replace('None', '')
                if siteMapCategory:
                    Spider_BaseClass.ProductUrlsAndCategory[productUrl] = siteMapCategory + " " + category
                else:
                    Spider_BaseClass.ProductUrlsAndCategory[productUrl] = category
        # try:
        #     nextPageUrl = categoryLinkResponse.xpath("//link[@rel='next']/@href").extract()[0]
        #     if not nextPageUrl.startswith(store_url):
        #         nextPageUrl = store_url.rstrip('/') + nextPageUrl
        #     self.listing(nextPageUrl, category)
        # except:
        #     pass

    def GetProducts(self, response):
        global productjson
        ignorProduct = self.IgnoreProduct(response)
        if ignorProduct == True:
            self.ProductIsOutofStock(GetterSetter.ProductUrl)
        else:
            global productjson
            productjson = HtmlResponse(url='None', body=response.text, encoding='utf-8')
            productjson = '{"products":[' + str(productjson.text).split('"products":[')[1].split(',"shippingDeliveryMessage"')[0] + '}'
            productjson = json.loads(productjson)
            productjson = productjson["products"][0]
            self.GetProductInfo(response)

    def GetName(self, response):
        name = productjson['displayName']
        return name

    def GetPrice(self, response):
        orignalPrice = productjson['listPrice']
        if orignalPrice != None:
            return float(str(orignalPrice).replace('$', '').replace(',', ''))
        else:
            return 0

    def GetSalePrice(self, response):
        salePrice = productjson.get('salePrice')
        if salePrice != None:
            return float(str(salePrice).replace("$", "").replace(',', ''))
        else:
            return 0

    def GetBrand(self, response):
        return 'Anna Taylor'

    def GetImageUrl(self, response):
        images = productjson['prodImageURL']
        return images
    def GetDescription(self, response):
        description = productjson['webLongDescription']
        return description

    def IgnoreProduct(self, response):
        if re.search('"availability":', response.text):
            productAvailability = response.text.split('"availability":')[1].split(',')[0].strip()
            print('productAvailability:', productAvailability)
            if not 'InStock' in productAvailability:
                return True
            else:
                return False

    def GetSizes(self, response):
        productSizes = []
        # gender = ProductFilters.objects.get(ProductUrl=GetterSetter.ProductUrl).ParentCategory.split(',')[0]
        for colors in productjson['skucolors']['colors']:
            colorName = colors['colorName']
            for size in colors['skusizes']['sizes']:
                available = size['available']
                sizeName = size['sizeAbbr']
                fitType = productjson['sizeType']
                sizelist = str(colorName), str(sizeName), available, str(fitType), 0.0, 0.0
                productSizes.append(sizelist)
        return productSizes

    def GetCategory(self, response):
        siteMapCategory = str(Spider_BaseClass.ProductUrlsAndCategory.get(GetterSetter.ProductUrl)).replace('None', '')
        return 'Women ' + siteMapCategory
