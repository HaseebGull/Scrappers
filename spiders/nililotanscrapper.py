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


class Nililotanscrapper(shopify):
    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(Nililotanscrapper, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        return spider

    def GetProductUrls(self, homePageResponse):
        # ========== Category And Subcategory ==========#
        topCategoryNodes = homePageResponse.xpath(
            "//ul[contains(@class,'nav-list-level-1')]/li/div[1]/ul[li[contains(text(),'Collection')]]")
        for topCategoryNode in topCategoryNodes:
            topCategoryTitle = topCategoryNode.xpath("./li/text()").get().strip()
            topCategorylink = topCategoryNode.xpath("./../../a/@href").get().strip()
            if not topCategorylink.startswith(store_url):
                topCategorylink = store_url.rstrip('/') + topCategorylink
            print("TOP CATEGORY  :", topCategoryTitle, ",TOP CATEGORY LINK  :", topCategorylink)
            categoryNodes = topCategoryNode.xpath("./li[a/span[contains(text(),'dresses')]]/a")
            for categoryNode in categoryNodes:
                categoryTitle = categoryNode.xpath("./span/text()").get().strip()
                categorylink = categoryNode.xpath("./@href").get()
                if not categorylink.startswith(store_url):
                    categorylink = store_url.rstrip('/') + categorylink
                print("CATEGORY  :", categoryTitle)
                if re.search('\?', categorylink):
                    categorylink = 'https' + categorylink.split('https' or 'http')[1].split('?')[0].strip()
                category = topCategoryTitle + " " + categoryTitle
                self.listing(categorylink, category)
        return Spider_BaseClass.AllProductUrls

    def listing(self, categorylink, category):
        categoryLinkResponse = requests.get(categorylink)
        categoryLinkResponse = HtmlResponse(url=categorylink, body=categoryLinkResponse.text, encoding='utf-8')
        # Product links with color
        product_list = categoryLinkResponse.xpath(
            "//div[contains(@class,'product-card-color-swatch ')]/@data-product-color-link").extract()
        for productUrl in product_list:
            if not productUrl.startswith(store_url):
                productUrl = store_url.rstrip('/') + productUrl
            productUrl = self.GetCanonicalUrl(productUrl)
            Spider_BaseClass.AllProductUrls.append(productUrl)
            print('productUrl:', productUrl)
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

    def GetProducts(self, response):
        try:
            ignorProduct = self.IgnoreProduct(response)
            if ignorProduct == True:
                self.ProductIsOutofStock(GetterSetter.ProductUrl)
            else:
                try:
                    global variantID
                    variantID = str(GetterSetter.ProductUrl).split('?variant=')[1]
                    shopify.ProductJson = json.loads(self.SetproductJson(response))
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
        print("Product Name: ", name)
        return name

    def GetSelectedColor(self, response):
        return response.xpath(
            "//div[@data-variant-id='" + variantID + "' and contains(@class,'selected')]/@data-variant-option1").get().strip()

    def GetPrice(self, response):
        for variantToken in shopify.productJson["variants"]:
            if str(variantToken["id"]) == str(variantID):
                if variantToken['compare_at_price'] and variantToken['compare_at_price'] != 0:
                    print("Original Price:", variantToken["compare_at_price"] / 100)
                    return variantToken['compare_at_price'] / 100
                else:
                    print("Original Price: ", variantToken["price"] / 100)
                    return variantToken["price"] / 100

    def GetSalePrice(self, response):
        for variantToken in shopify.productJson["variants"]:
            if str(variantToken["id"]) == str(variantID):
                print("Price: ", variantToken["price"] / 100)
                return variantToken["price"] / 100
        return 0

    def GetImageUrl(self, response):
        imagesUrls = []
        color = self.GetSelectedColor(response)
        for imageToken in shopify.productJson["media"]:
            if str(imageToken["alt"]) == str(color):
                imageUrl = imageToken["src"]
                print("ImageUrl: ", imageUrl)
                imagesUrls.append(imageUrl)
        return imagesUrls

    def GetSizes(self, response):
        color = self.GetSelectedColor(response)
        sizes = shopify.GetSizes(self, response)
        selectedColSizes = Enumerable(sizes).where(lambda x: x[0] == color).to_list()
        print("Sizes: ", selectedColSizes)
        return selectedColSizes
