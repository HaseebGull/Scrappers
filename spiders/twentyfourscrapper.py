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


class TwentyFourScrapper(Spider_BaseClass):
    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(TwentyFourScrapper, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        return spider

    def GetProductUrls(self, homePageResponse):
        # ========== Category And Subcategory ==========#
        topCategoryNodes = homePageResponse.xpath(
            "//nav[contains(@class,'nav-gender')]/a[contains(text(),'Women') or contains(text(),'Men')]")
        for topCategoryNode in topCategoryNodes:
            topCategoryTitle = topCategoryNode.xpath("./text()").get().strip()
            topCategorylink = topCategoryNode.xpath("./@href").get()
            if not topCategorylink.startswith(store_url):
                topCategorylink = store_url.rstrip('/').replace('/en-us', '') + topCategorylink
            topCategorylinkResponse = requests.get(topCategorylink)
            topCategorylinkResponse = HtmlResponse(url=topCategorylink, body=topCategorylinkResponse.text,
                                                   encoding='utf-8')
            print(topCategoryTitle)
            categoryNodes = topCategorylinkResponse.xpath("//ul[@id='" + str(
                topCategoryTitle).lower() + "-nav']/li[span[contains(a/text(),'New') or contains(a/text(),'Ready') or contains(a/text(),'Sale')]]")
            for categoryNode in categoryNodes:
                categoryTitle = categoryNode.xpath("./span/a/text()").get().strip()
                categorylink = categoryNode.xpath("./span/a/@href").get()
                if not categorylink.startswith(store_url):
                    categorylink = store_url.rstrip('/').replace('/en-us', '') + categorylink

                subCategoryNodes = categoryNode.xpath(
                    "./div//div/ul/li/a[contains(text(),'Dress') or contains(text(),'Jumpsuit') or contains(text(),'Suit')]")
                if not subCategoryNodes:
                    category = topCategoryTitle + " " + categoryTitle
                    self.listing(categorylink, category)
                else:
                    for subCategoryNode in subCategoryNodes:
                        subCategoryTitle = subCategoryNode.xpath("./text()").get().strip()
                        subCategorylink = subCategoryNode.xpath("./@href").get()
                        if not subCategorylink.startswith(store_url):
                            subCategorylink = store_url.rstrip('/').replace('/en-us', '') + subCategorylink
                        category = topCategoryTitle + " " + categoryTitle + " " + subCategoryTitle
                        self.listing(subCategorylink, category)
        return Spider_BaseClass.AllProductUrls

    def listing(self, categorylink, category):
        categoryLinkResponse = requests.get(categorylink, stream=True)
        categoryLinkResponse = HtmlResponse(url=categorylink, body=categoryLinkResponse.text, encoding='utf-8')
        product_list = categoryLinkResponse.xpath(
            "//a[@class='item']/@href").extract()
        for productUrl in product_list:
            if not productUrl.startswith(store_url):
                productUrl = store_url.rstrip('/').replace('/en-us', '') + productUrl
            Spider_BaseClass.AllProductUrls.append(productUrl)
            siteMapCategory = str(Spider_BaseClass.ProductUrlsAndCategory.get(productUrl)).replace('None', '')
            if siteMapCategory:
                Spider_BaseClass.ProductUrlsAndCategory[productUrl] = siteMapCategory + " " + category
            else:
                Spider_BaseClass.ProductUrlsAndCategory[productUrl] = category
        try:
            nextPageUrl = categoryLinkResponse.xpath(
                "//link[@rel='next']/@href").extract()[0]
            if not nextPageUrl.startswith(store_url):
                nextPageUrl = store_url.rstrip('/') + nextPageUrl
            self.listing(nextPageUrl, category)
        except:
            pass

    def GetProducts(self, response):
        global productjson
        global sku
        global offerID
        ignorProduct = self.IgnoreProduct(response)
        if ignorProduct == True:
            self.ProductIsOutofStock(GetterSetter.ProductUrl)
        else:
            jsonStr = response.xpath("//script[@id='__NEXT_DATA__']/text()").get()
            productjson = json.loads(jsonStr)
            if re.search('"sku": "', response.text):
                sku = response.text.split('"sku": "')[1].split('",')[0].strip()
            offerID = productjson['props']['initialState']['entities']['product'][sku]['offerId']

            categoryAndName =self.GetCategory(response) + " " + self.GetName(response)
            if (re.search('Sale', categoryAndName, re.IGNORECASE) or
                re.search('New Arrivals', categoryAndName, re.IGNORECASE)) and not \
                    re.search(r'\b((shirt(dress?)|jump(suit?)|dress|gown|suit|caftan)(s|es)?)\b', categoryAndName,
                              re.IGNORECASE):
                print('Skipping Non Dress Product')
                self.ProductIsOutofStock(GetterSetter.ProductUrl)
            else:
                self.GetProductInfo(response)

    def IgnoreProduct(self, response):
        if re.search('"availability":"', response.text) and not re.search('InStock',
                                                                          response.text.split('"availability":"')
                                                                          [1].split('"}}')[0].strip()):
            return True

        if response.xpath("//button[@type='button' and contains(text(),'This product is no longer available.')]"):
            return True

        return False

    def GetName(self, response):
        try:
            color = self.GetSelectedColor(response)
            name = str(response.xpath("//h1[contains(@class,'item-product')]/span/text()").get()).strip()
            if not color == '' and not re.search(color, name, re.I):
                name = name + " - " + color
            return name
        except:
            return str(response.xpath("//h1[contains(@class,'item-product')]/span/text()").get()).strip()

    def GetSelectedColor(self, response):
        selectdColor = response.xpath(
            "//div[@class='item-color']/div/p/span[2]/text()").get()
        if selectdColor:
            return selectdColor
        else:
            return str(response.xpath(
                "//div[@class='accordion-text']/ul/li[contains(span/text(),'Color')]/text()")
                       .get()).replace(':', '').strip()

    def GetPrice(self, response):
        orignalPrice = productjson['props']['initialState']['entities']['offer'][offerID]['priceInclVat']
        if orignalPrice != None:
            return float(orignalPrice / 100)
        else:
            return 0

    def GetSalePrice(self, response):

        salePrice = productjson['props']['initialState']['entities']['offer'][offerID]['discountPriceInclVat']
        if salePrice != None:
            return float(salePrice / 100)
        else:
            return 0.0

    def GetBrand(self, response):
        return str(response.xpath("//a[contains(@class,'item-brand')]/text()").get()).strip()

    def GetImageUrl(self, response):
        imageUrls = []
        images = response.xpath("//div[contains(@class,'slick-horizontal')]/div/div//picture/img/@src").extract()
        for image in images:
            imageUrls.append(image)
        return imageUrls

    def GetDescription(self, response):
        descriptionJToken = productjson['props']['initialState']['entities']['product'][sku]['bulletPoints']
        description = ','.join(descriptionJToken)
        try:
            material = productjson['props']['initialState']['entities']['product'][sku]['productInformation'][
                'composition']
            return description + " " + material
        except:
            return description

    def GetSizes(self, response):

        productSizes = []
        colorName = self.GetSelectedColor(response)
        sizeJToken = productjson['props']['initialState']['entities']['product'][sku]['sizeAvailable']
        gender = ProductFilters.objects.get(ProductUrl=GetterSetter.ProductUrl).ParentCategory.split(',')[0]
        for size in sizeJToken:
            sizeName = size['sizeLabel']
            available = size['hasOffer']
            fitType = GetFitType(gender, sizeName)
            sizelist = str(colorName), str(sizeName), available, str(fitType), 0.0, 0.0
            productSizes.append(sizelist)
        return productSizes

    def GetCategory(self, response):
        filterList = []
        siteMapCategory = str(Spider_BaseClass.ProductUrlsAndCategory.get(GetterSetter.ProductUrl)).replace('None', '')
        categoryJToken = productjson['props']['initialState']['entities']['product'][sku]['hierarchicalCategories']
        for category in categoryJToken:
            filterList.append(category['label'])
        filters = '$'.join(map(str, filterList))
        return siteMapCategory + " " + filters
