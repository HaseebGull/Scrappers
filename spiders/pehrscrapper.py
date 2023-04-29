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
class PehrScrapper(shopify):
    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(PehrScrapper, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        return spider

    def GetProductUrls(self, homePageResponse):

        # ========== Category And Subcategory ==========#
        topCategoryNodes = homePageResponse.xpath(
            "//ul[@class='header-main__items']/li/div[a[contains(text(),'Organic Clothing')]]")
        for topCategoryNode in topCategoryNodes:
            topCategoryTitle = topCategoryNode.xpath("./a/text()").get().strip()
            topCategorylink = topCategoryNode.xpath("./a/@href").get()
            if not topCategorylink.startswith(store_url):
                topCategorylink = store_url.rstrip('/') + topCategorylink
            categoryNodes = topCategoryNode.xpath(
                "./div/ul/li[a[contains(text(),'Style')]]")
            for categoryNode in categoryNodes:
                categoryTitle = categoryNode.xpath("./a/text()").get().strip()
                categorylink = categoryNode.xpath("./a/@href").get()
                if not categorylink.startswith(store_url):
                    categorylink = store_url.rstrip('/') + categorylink
                subCategoryNodes = categoryNode.xpath(
                    "./ul/li/a[not(contains(text(),'Pant')) and not(contains(text(),'Tops')) and not(contains(text(),'Hat')) and not(contains(text(),'Bibs')) and not(contains(text(),'All'))]")
                for subCategoryNode in subCategoryNodes:
                    subCategoryTitle = subCategoryNode.xpath("./text()").get().strip()
                    subCategorylink = subCategoryNode.xpath("./@href").get()
                    if not subCategorylink.startswith(store_url):
                        subCategorylink = store_url.rstrip('/') + subCategorylink
                    # =================== BREADCRUM ===================3
                    category = topCategoryTitle + " " + categoryTitle + " " + subCategoryTitle
                    # ======================================#
                    self.listing(subCategorylink, category)
        return Spider_BaseClass.AllProductUrls

    def listing(self, categorylink, category):
        CategoryLinkResponse = requests.get(categorylink)
        categoryPageResponse = HtmlResponse(url=categorylink, body=CategoryLinkResponse.text, encoding='utf-8')
        product_list = categoryPageResponse.xpath(
            "//div[@class='cProductCard']/a/@href").extract()
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
        try:
            ignorProduct = self.IgnoreProduct(response)
            if ignorProduct == True:
                self.ProductIsOutofStock(GetterSetter.ProductUrl)
            else:
                try:
                    global variantID
                    variantID = str(GetterSetter.ProductUrl).split('?variant=')[1]
                    shopify.productJson = json.loads(self.SetproductJson(response))
                    self.GetProductInfo(response)
                except:
                    pass
        except Exception as e:
            self.ExceptionHandlineInGetProductInfo(e, 'GetProductsError',
                                                   'Exception: Exception in GetProducts function.')
            return

    def SetproductJson(self, response):
        productApiUrl = response.xpath("//link[@rel='canonical']/@href").get().strip()
        print("Invoke product json api")
        return requests.get(productApiUrl + '.js', cookies=shopify.cookiesDict).content

    def GetName(self, response):
        color = self.GetSelectedColor(response)
        name = shopify.GetName(self, response) + " - " + color
        return name

    def GetSelectedColor(self, response):
        color = ''
        for variantToken in shopify.productJson["variants"]:
            if str(variantToken["id"]) == str(variantID):
                color = variantToken['option1']
        return color

    def GetPrice(self, response):
        for variantToken in shopify.productJson["variants"]:
            if str(variantToken["id"]) == str(variantID):
                if variantToken['compare_at_price'] and variantToken['compare_at_price'] != 0:
                    return variantToken['compare_at_price'] / 100
                else:
                    return variantToken["price"] / 100

    def GetSalePrice(self, response):
        for variantToken in shopify.productJson["variants"]:
            if str(variantToken["id"]) == str(variantID):
                return variantToken["price"] / 100
        return 0

    def GetImageUrl(self, response):
        imagesUrls = []
        color = self.GetSelectedColor(response)
        images = response.xpath(
            "//div[contains(@class,'cImg--image cImg-size--960') and contains(@style, '" + str(
                color) + "')]/@style").extract()
        for image in images:
            imagesUrls.append(str(image).lstrip("background-image: url('").rstrip("');"))
        return imagesUrls

    def GetSizes(self, response):
        color = self.GetSelectedColor(response)
        sizes = shopify.GetSizes(self, response)
        selectedColSizes = Enumerable(sizes).where(lambda x: x[0] == color).to_list()
        return selectedColSizes

    def IgnoreProduct(self, response):
        if re.search('"availability":', response.text):
            productAvailability = response.text.split('"availability":')[1].split(',')[0].strip()
            if not 'InStock' in productAvailability:
                return True
            else:
                return False
