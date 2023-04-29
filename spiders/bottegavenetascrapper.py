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


class BottegaVenetaScrapper(Spider_BaseClass):
    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(BottegaVenetaScrapper, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        return spider

    def GetProductUrls(self, homePageResponse):
        # ========== Category And Subcategory ==========#
        topCategoryNodes = homePageResponse.xpath(
            "//ul[contains(@class,'c-nav__level1')]/li[a[contains(span/text(),'Women')]]")
        for topCategoryNode in topCategoryNodes:
            topCategoryTitle = topCategoryNode.xpath("./a/span/text()").get().strip()
            topCategorylink = topCategoryNode.xpath("./a/@href").get()
            if not topCategorylink.startswith(store_url):
                topCategorylink = store_url.rstrip('/') + topCategorylink
            print("TOP CATEGORY  :", topCategoryTitle, "TOP CATEGORY LINK  :", topCategorylink)
            categoryNodes = topCategoryNode.xpath(
                "./div[@data-ref='subnav']/ul[contains(@class,'c-nav__level2')]/li[a[contains(text(),'Clothing')]]")
            for categoryNode in categoryNodes:
                categoryTitle = categoryNode.xpath("./a/text()").get().strip()
                categorylink = categoryNode.xpath("./a/@href").get()
                if not categorylink.startswith(store_url):
                    categorylink = store_url.rstrip('/') + categorylink
                print("CATEGORY  :", categoryTitle, "CATEGORY LINK  :", categorylink)
                if re.search('\?', categorylink):
                    categorylink = 'https' + categorylink.split('https' or 'http')[1].split('?')[0].strip()
                subCategoryNodes = categoryNode.xpath(
                    "./div[contains(@class,'subsubnav')]/ul[contains(@class,'c-nav__level3')]/li/a[contains(text(),'Dresses')]")
                for subCategoryNode in subCategoryNodes:
                    subCategoryTitle = subCategoryNode.xpath("./text()").get().strip()
                    subCategorylink = subCategoryNode.xpath("./@href").get()
                    if not subCategorylink.startswith(store_url):
                        subCategorylink = store_url.rstrip('/') + subCategorylink
                    print("SUB CATEGORY  :", subCategoryTitle, "SUB CATEGORY LINK  :", subCategorylink)
                    if re.search('\?', subCategorylink):
                        subCategorylink = 'https' + subCategorylink.split('https' or 'http')[1].split('?')[0].strip()
                    category = categoryTitle + " " + categoryTitle + " " + subCategoryTitle
                    self.listing(subCategorylink, category)
        return Spider_BaseClass.AllProductUrls

    def listing(self, subCategorylink, category):
        subCategoryLinkResponse = requests.get(subCategorylink)
        subCategoryLinkResponse = HtmlResponse(url=subCategorylink, body=subCategoryLinkResponse.text, encoding='utf-8')
        product_list = subCategoryLinkResponse.xpath(
            "//a[contains(@class,'c-product__link')]/@href").extract()
        for productUrl in product_list:
            if not productUrl.startswith(store_url):
                productUrl = store_url.rstrip('/') + productUrl
            print('Product Url: ', productUrl)
            Spider_BaseClass.AllProductUrls.append(productUrl)
            siteMapCategory = str(Spider_BaseClass.ProductUrlsAndCategory.get(productUrl)).replace('None', '')
            if siteMapCategory:
                Spider_BaseClass.ProductUrlsAndCategory[productUrl] = siteMapCategory + " " + category
            else:
                Spider_BaseClass.ProductUrlsAndCategory[productUrl] = category
        try:
            nextPageUrl = subCategoryLinkResponse.xpath("//button[@class='c-loadmore__btn']/@data-url").extract()[0]
            print('nextPageUrl:', nextPageUrl)
            if not nextPageUrl.startswith(store_url):
                nextPageUrl = store_url.rstrip('/') + nextPageUrl
            self.listing(nextPageUrl, category)
        except:
            pass

    def GetProducts(self, response):
        global productjson
        responseJson = response.xpath("//script[@type='application/ld+json']/text()").get()
        productjson = json.loads(responseJson)
        self.GetProductInfo(response)

    def GetName(self, response):
        color = self.GetSelectedColor(response)
        name = response.xpath("//h1[contains(@class,'c-product__name')]/text()").get()
        if not color == '' and not re.search(color, name):
            name = name + " - " + color
        return name

    def GetSelectedColor(self, response):
        color = ''
        if re.search('- Color:', productjson['description']):
            color = str(productjson['description']).split('- Color:')[1].split('- ')[0]
            if re.search('<', color):
                color = str(color).split('<')[0]
        return (color.replace('&nbsp;', '')).strip()

    def GetPrice(self, response):
        # price = response.xpath("//span[@id='price-value']/text()").get()
        # price = response.xpath("//s[@id='price-value-additional']/text()").get() #NONE
        orignalPrice = response.xpath(
            "//p[contains(@class,'__pricing')]/s[contains(@class,'pricing-original')]/text()").get()
        if orignalPrice != None:
            return float(str(orignalPrice).replace('$', '').replace(',', ''))
        else:
            regularPrice = response.xpath(
                "//p[contains(@class,'__pricing')]/span[contains(@class,'pricing-current')]/text()").get()
            return float(str(regularPrice).replace('$', '').replace(',', ''))

    def GetSalePrice(self, response):
        salePrice = response.xpath(
            "//p[contains(@class,'__pricing')]/span[contains(@class,'pricing-current')]/text()").get()
        if salePrice != None:
            return float(str(salePrice).replace("$", "").replace(',', ''))
        else:
            return 0

    def GetBrand(self, response):
        return productjson['brand']

    def GetImageUrl(self, response):
        itemID = ''
        imageUrls = []
        if re.search('ItemId: ', response.text):
            itemID = response.text.split('ItemId: ')[1].split(',')[0]
        if re.search('var image_data' + itemID + ' = \[', response.text):
            imagesList = '[' + response.text.split('var image_data' + itemID + ' = [')[1].split('var')[0]
            imageJson = json.loads(imagesList)
            for image in imageJson:
                imageurl = image['image_data'][0]
                imageUrls.append(store_url.rstrip('/') + imageurl)
        return imageUrls

    def GetDescription(self, response):
        return productjson['description']

    def GetSizes(self, response):
        productSizes = []
        sku = productjson['sku']
        colorName = self.GetSelectedColor(response)
        sizeOptions = response.xpath("//input[@data-attribute='size' or @data-attribute='Size']/@value").extract()
        for size in sizeOptions:
            prodId = sku + '_' + size

            for sizeValue in productjson['offers']:
                if sizeValue['sku'] == prodId:
                    if 'InStock' in sizeValue['availability']:
                        available = True
                        sizelist = str(colorName), str(size), available, 0.0, 0.0
                        productSizes.append(sizelist)
                        break

        return productSizes

    def IgnoreProduct(self, response):
        if re.search('"availability":', response.text):
            productAvailability = response.text.split('"availability":')[1].split(',')[0].strip()
            if not 'InStock' in productAvailability:
                return True
            else:
                return False

    def GetCategory(self, response):
        filterList = []
        if GetterSetter.ProductUrl in Spider_BaseClass.ProductUrlsAndCategory:
            categories = Spider_BaseClass.ProductUrlsAndCategory[GetterSetter.ProductUrl]
            for category in str(categories).split('$'):
                filterList.append(category)
        filters = '$'.join(map(str, filterList))
        return filters
