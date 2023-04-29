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


class YooxScrapper(Spider_BaseClass):
    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(YooxScrapper, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        return spider

    def GetProductUrls(self, homePageResponse):
        # ========== Category And Subcategory ==========#
        gendrNodes = homePageResponse.xpath(
            "//div[@class='banners-splash-wrapper']/a[contains(span/text(),'WOMEN') or contains(span/text(),'MEN') or contains(span/text(),'KIDS')]")
        for gendrNode in gendrNodes:
            genderTitle = gendrNode.xpath("./span/text()").get().strip()
            genderlink = gendrNode.xpath("./@href").get()
            if not genderlink.startswith(store_url):
                genderlink = store_url.rstrip('/') + genderlink
            genderLinkResponse = requests.get(genderlink)
            genderLinkResponse = HtmlResponse(url=genderlink, body=genderLinkResponse,
                                              encoding='utf-8')

            categoryNodes = genderLinkResponse.xpath(
                "//ul[@id='sections-menu']/li[contains(span/text(),'Clothing')]")
            for categoryNode in categoryNodes:
                categoryTitle = categoryNode.xpath("./span/text()").get().strip()
                subCategoryTag = categoryNode.xpath("./span/@data-ref").get()

                subCategoryNodes = genderLinkResponse.xpath(
                    "//div[contains(@id,'js-" + subCategoryTag + "')]/div/div//div[contains(text(),'CATEGORIES')]/following-sibling::div/div/a[contains(text(),'Dress') or contains(text(),'Jumpsuits')]")
                for subCategoryNode in subCategoryNodes:
                    subCategoryTitle = subCategoryNode.xpath("./text()").get().strip()
                    subCategorylink = subCategoryNode.xpath("./@href").get()
                    if not subCategorylink.startswith(store_url):
                        subCategorylink = store_url.rstrip('/') + subCategorylink
                    category = genderTitle + " " + categoryTitle + " " + subCategoryTitle
                    self.listing(subCategorylink, category)
        return Spider_BaseClass.AllProductUrls

    def listing(self, categorylink, category):
        CategoryLinkResponse = requests.get(categorylink)
        CategoryLinkResponse = HtmlResponse(url=categorylink, body=CategoryLinkResponse.text,
                                            encoding='utf-8')
        productListingJsonStr = CategoryLinkResponse.xpath(
            "//div[@data-controller='catalog']/@data-catalog-products-value").get()
        apiresponse = json.loads(productListingJsonStr)
        self.GetUrls(apiresponse, category)
        nextPageUrl = apiresponse['_links']['next']
        while nextPageUrl != None:
            if not nextPageUrl.startswith(store_url):
                nextPageUrl = store_url.rstrip('/') + apiresponse['url']
            CategoryLinkResponse = requests.get(nextPageUrl)
            CategoryLinkResponse = HtmlResponse(url=categorylink, body=CategoryLinkResponse.text,
                                                encoding='utf-8')
            productListingJsonStr = CategoryLinkResponse.xpath(
                "//div[@data-controller='catalog']/@data-catalog-products-value").get()
            apiresponse = json.loads(productListingJsonStr)
            nextPageUrl = apiresponse['_links']['next']
            self.GetUrls(apiresponse, category)

    def GetUrls(self, dataJson, category):
        for apiproduct in dataJson['items']:
            productUrl = str(apiproduct['_links']['self']['href']).replace('\\', '')
            Spider_BaseClass.AllProductUrls.append(productUrl)
            siteMapCategory = str(Spider_BaseClass.ProductUrlsAndCategory.get(productUrl)).replace('None', '')
            if siteMapCategory:
                Spider_BaseClass.ProductUrlsAndCategory[productUrl] = siteMapCategory + " " + category
            else:
                Spider_BaseClass.ProductUrlsAndCategory[productUrl] = category

    def GetProducts(self, response):
        global productjson
        ignorProduct = self.IgnoreProduct(response)
        if ignorProduct == True:
            self.ProductIsOutofStock(GetterSetter.ProductUrl)
        else:
            productJsonStr = response.xpath(
                "//div[@data-controller='product']/@data-product-json-value").get()
            productjson = json.loads(productJsonStr)
            self.GetProductInfo(response)

    def IgnoreProduct(self, response):
        if re.search('"availability":"', response.text):
            productAvailability = response.text.split('"availability":"')[1].split('"}}')[0].strip()
            if not 'InStock' in productAvailability or 'PreOrder' in productAvailability:
                return True
            else:
                return False

    def GetName(self, response):
        color = self.GetSelectedColor(response)
        name = productjson.get('name')
        if not color == '' and not re.search(color, name, re.I):
            name = name + " - " + color
        return name

    def GetSelectedColor(self, response):
        return productjson.get('name')

    def GetPrice(self, response):
        try:
            orignalPrice = productjson['originalPrice']['amount'] / 100
            if orignalPrice != None:
                return float(str(orignalPrice).replace('$', '').replace(',', ''))
        except:
            regularPrice = productjson['price']['amount'] / 100
            return float(str(regularPrice).replace('$', '').replace(',', ''))

    def GetSalePrice(self, response):
        salePrice = productjson['price']['amount'] / 100
        if salePrice != None:
            return float(str(salePrice).replace("$", "").replace(',', ''))
        else:
            return 0

    def GetBrand(self, response):
        return productjson['brands'][0]['name']

    def GetImageUrl(self, response):
        imageUrls = []
        images = productjson['images']
        for image in images:
            imageUrls.append(image['_links']['xlarge']['href'])
        return imageUrls

    def GetDescription(self, response):
        return productjson['description']

    def GetSizes(self, response):
        productSizes = []
        colorName = self.GetSelectedColor(response)
        sizeOptions = productjson['variants']
        gender = ProductFilters.objects.get(ProductUrl=GetterSetter.ProductUrl).ParentCategory.split(',')[0]
        for sizeOption in sizeOptions:
            if sizeOption['isAvailable'] == True:
                sizeName = sizeOption['optionValues'][0]['value']
                fitType = GetFitType(gender, sizeName)
                available = True
                sizelist = str(colorName), str(sizeName), available, str(fitType), 0.0, 0.0
                productSizes.append(sizelist)
        return productSizes

    def GetCategory(self, response):
        siteMapCategory = str(Spider_BaseClass.ProductUrlsAndCategory.get(GetterSetter.ProductUrl)).replace('None', '')
        return siteMapCategory
