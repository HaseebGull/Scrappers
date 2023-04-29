import re
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
from seleniumfile import *


class LoftScrapper(Spider_BaseClass):
    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(LoftScrapper, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        return spider

    def GetProductUrls(self, homePageResponse):
        seleniumResponse = SeleniumResponse(store_url)
        # ========== Category And Subcategory ========== #
        topCategoryNodes = seleniumResponse.xpath(
            "//div[@role='menubar']/div[a[contains(strong/text(),'New')]]")
        for topCategoryNode in topCategoryNodes:
            topCategoryTitle = topCategoryNode.xpath("./a/strong/text()")
            if topCategoryTitle:
                topCategoryTitle = topCategoryTitle.get().strip()
            else:
                topCategoryTitle = topCategoryNode.xpath("./a/strong/div/text()").get().strip()
            # topCategorylink = topCategoryNode.xpath("./a/@href").get()
            # if not topCategorylink.startswith(store_url):
            #     topCategorylink = store_url.rstrip('/') + topCategorylink
            categoryNodes = topCategoryNode.xpath(
                "./nav/div/div/a[contains(text(),'Dress') or contains(text(),'Midi & Maxi') or contains(text(),'Jumpsuits')]")
            for categoryNode in categoryNodes:
                categoryTitle = categoryNode.xpath(".//text()").get().strip()
                categorylink = categoryNode.xpath("./@href").get()
                if not categorylink.startswith(store_url):
                    categorylink = store_url.rstrip('/') + categorylink
                # =================== BREADCRUM ===================3
                category = topCategoryTitle + " " + categoryTitle
                print(category)
                # ======================================#
                self.listing(categorylink, category)
        return Spider_BaseClass.AllProductUrls

    def listing(self, categorylink, category):
        # CategoryLinkResponse = requests.get(categorylink)
        # categoryPageResponse = HtmlResponse(url=categorylink, body=CategoryLinkResponse.text, encoding='utf-8',
        #                                     headers=Spider_BaseClass.headersDict)
        categoryPageResponse = SeleniumResponse(categorylink)
        product_list = categoryPageResponse.xpath(
            "//div[@class='product-wrap']/div/a/@href").extract()
        for productUrl in product_list:
            if not productUrl.startswith(store_url):
                productUrl = store_url.rstrip('/') + productUrl
            print(productUrl)
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

    def GetCategories(self, response):
        url = response.request.url
        ConvertedResponse = SeleniumResponse(url)
        Spider_BaseClass.AllProductUrl = list(set(self.GetProductUrls(ConvertedResponse)))

        print('DB Urls', len(Spider_BaseClass.db_urls))
        print('Web Urls', len(Spider_BaseClass.AllProductUrl))
        print('DB & Web Urls', len(Spider_BaseClass.AllProductUrl) + len(Spider_BaseClass.db_urls))

        Spider_BaseClass.TotalDistinctProductUrl = list(set(Spider_BaseClass.AllProductUrl + Spider_BaseClass.db_urls))
        print('Distinct Urls', len(Spider_BaseClass.TotalDistinctProductUrl))

        Product.objects.filter(StoreId=store_id).update(UpdatedOrAddedOnLastRun=0)

        for productUrl in Spider_BaseClass.TotalDistinctProductUrl:
            try:
                GetterSetter.ProductUrl = productUrl
                # productres = requests.get(productUrl, cookies=Spider_BaseClass.cookiesDict,
                #                           headers=Spider_BaseClass.headersDict)
                # productResponse = HtmlResponse(url=productUrl, body=productres.text, encoding='utf-8')
                productResponse = SeleniumResponse(productUrl)
                self.GetProducts(productResponse)
            except Exception as e:
                self.ExceptionHandlineInGetProductInfo(e, 'GetProductsError',
                                                       'Exception: Exception in GetProducts function.')
                continue

    def GetProducts(self, response):
        ignorProduct = self.IgnoreProduct(response)
        if ignorProduct == True:
            self.ProductIsOutofStock(GetterSetter.ProductUrl)
        global productJson
        productJson = json.loads(self.SetProductJson(response))
        categoryAndName = self.GetCategory(response) + " " + self.GetName(response)
        if (re.search('sale', categoryAndName, re.IGNORECASE) or
            re.search('new arrival', categoryAndName, re.IGNORECASE)) and not \
                re.search(r'\b((shirt(dress?)|jump(suit?)|dress|gown|romper|suit|caftan)(s|es)?)\b', categoryAndName,
                          re.IGNORECASE):
            print('Skipping Non Dress Product')
            self.ProductIsOutofStock(GetterSetter.ProductUrl)
        else:
            self.GetProductInfo(response)

    def IgnoreProduct(self, response):
        productAvailability = response.xpath("//div[@class='sold-out-details']/h3/text()")
        if productAvailability:
            if 'Out of Stock' in productAvailability.get().strip():
                return True
            else:
                return False

    def SetProductJson(self, response):
        productJson = response.text.split('var productIndex =')[1].split('var priceList')[0].strip()
        return productJson

    def GetName(self, response):
        return productJson['products'][0]['displayName']

    def GetSelectedColor(self, response):
        return response.xpath(
            "//div[contains(@class,'product-sections') and contains(div/text(),'Color')]/span[contains(@class,'selectedColor')]/text()").get()

    def GetPrice(self, response):
        return productJson['products'][0]['listPrice']

    def GetSalePrice(self, response):
        try:
            print('SALE PRICE ', productJson['products'][0]['salePrice'])
            return productJson['products'][0]['salePrice']
        except:
            return 0.0

    def GetBrand(self, response):
        return 'Loft'

    def GetImageUrl(self, response):
        imageUrls = []
        image = productJson['products'][0]['prodImageURL']
        if image:
            if re.search("\?", image):
                imageApiUrl = str(image).split("?")[0]
                imageApi = imageApiUrl + '_IS?req=set,json'
                imageApiResp = requests.get(imageApi)
                imageJsonStr = imageApiResp.text.lstrip('/*jsonp*/s7jsonResponse(').rstrip(',"");')
                imageJson = json.loads(imageJsonStr)
                images = imageJson['set']['item']
                for image in images:
                    imageUrls.append(imageApiUrl.split('LO')[0] + image['i']['n'])
                return imageUrls
        else:
            raise NotImplementedError('NO Images Found')
        return productJson['products'][0]['prodImageURL']

    def GetDescription(self, response):
        description = productJson['products'][0]['webLongDescription']
        fabricationContent = productJson['products'][0]['fabricationContent']
        garmentCare = productJson['products'][0]['garmentCare']
        fabric = productJson['products'][0]['bulletPointB']
        category = productJson['products'][0]['bulletPointC']
        description = description + " " + fabricationContent + " " + garmentCare + " " + fabric + " " + category
        return description

    def GetSizes(self, response):
        productSizes = []
        productJsonSizes = productJson['products'][0]['skucolors']['colors']
        gender = ProductFilters.objects.get(ProductUrl=GetterSetter.ProductUrl).ParentCategory.split(',')[0]
        for productJsonSize in productJsonSizes:
            colorName = productJsonSize['colorName']
            colorSizes = productJsonSize['skusizes']['sizes']
            for colorSizes in colorSizes:
                sizeName = colorSizes['fullSizeName']
                fitType = GetFitType(gender, sizeName)
                available = colorSizes['available']
                sizelist = str(colorName), str(sizeName), available, str(fitType), 0.0, 0.0
                productSizes.append(sizelist)
        return productSizes

    def GetCategory(self, response):
        siteMapCategory = str(Spider_BaseClass.ProductUrlsAndCategory.get(GetterSetter.ProductUrl)).replace('None', '')
        return 'Women ' + siteMapCategory
