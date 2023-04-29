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


class MissguidedScrapper(Spider_BaseClass):
    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(MissguidedScrapper, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        return spider

    def GetProductUrls(self, homePageResponse):
        # ========== Category And Subcategory ==========#
        topCategoryNodes = homePageResponse.xpath(
            "//div[@class='cont'][div[@class='flex']/div[contains(@data-id,'category-3')]]")
        for topCategoryNode in topCategoryNodes:
            topCategoryTitle = topCategoryNode.xpath("./div/div/a/h5/text()").get().strip()
            topCategorylink = topCategoryNode.xpath("./div/div/a/@href").get()
            if not topCategorylink.startswith(store_url):
                topCategorylink = store_url.rstrip('/') + topCategorylink
            print("TOP CATEGORY  :", topCategoryTitle, "TOP CATEGORY LINK  :", topCategorylink)
            categoryNodes = topCategoryNode.xpath(
                "./div[@class='dropdown-container']/div[contains(@class,'category-3')]/div/ul/li/a[not (contains(text(),'view all'))]")
            for categoryNode in categoryNodes:
                categoryTitle = categoryNode.xpath("./text()").get().strip()
                categorylink = categoryNode.xpath("./@href").get()
                if not categorylink.startswith(store_url):
                    categorylink = store_url.rstrip('/') + categorylink
                print("CATEGORY  :", categoryTitle, "CATEGORY LINK  :", categorylink)
                if re.search('\?', categorylink):
                    categorylink = 'https' + categorylink.split('https' or 'http')[1].split('?')[0].strip()

                self.listing(categorylink, categoryTitle, store_url)
        return Spider_BaseClass.AllProductUrls

    def listing(self, categorylink, category, store_url):
        CategoryLinkResponse = requests.get(categorylink)
        CategoryLinkResponse = HtmlResponse(url=categorylink, body=CategoryLinkResponse.text, encoding='utf-8')
        apiUrl = 'https://43gpw0.a.searchspring.io/api/search/search.json?ajaxCatalog=v3&resultsFormat=native&siteId=43gpw0&domain=https://www.blueandcream.com/category/w_Dresses.html&bgfilter.catcode=w_Dresses&q=&page=1'
        apiresponse = requests.get(url=apiUrl, timeout=6000)
        apiresponseJson = json.loads(apiresponse.content)
        totalPage = apiresponseJson['pagination']['totalPages']
        pageNo = 2

        self.GetUrls(apiresponseJson, category)

        while pageNo <= totalPage:
            nextPageUrl = 'https://43gpw0.a.searchspring.io/api/search/search.json?ajaxCatalog=v3&resultsFormat=native&siteId=43gpw0&domain=https://www.blueandcream.com/category/w_Dresses.html&bgfilter.catcode=w_Dresses&q=&page=' + str(
                pageNo) + ''
            apiresponse = requests.get(url=nextPageUrl, timeout=6000)
            apiresponseJson = json.loads(apiresponse.content)
            self.GetUrls(apiresponseJson, category)
            pageNo = pageNo + 1

    def GetUrls(self, datJson, category):
        for proNode in datJson['results']:
            catJsosn = proNode['category']
            category = '$'.join(map(str, catJsosn))
            productUrl = proNode['url']
            if not productUrl.startswith(store_url):
                productUrl = store_url.rstrip('/') + productUrl
            print('PRODUCT URL : ', productUrl)
            Spider_BaseClass.AllProductUrls.append(productUrl)
            siteMapCategory = str(Spider_BaseClass.ProductUrlsAndCategory.get(productUrl)).replace('None', '')
            if siteMapCategory:
                Spider_BaseClass.ProductUrlsAndCategory[productUrl] = siteMapCategory + " " + category
            else:
                Spider_BaseClass.ProductUrlsAndCategory[productUrl] = category

    def GetProducts(self, response):
        global productjson
        responseJson = response.xpath("//script[@type='application/ld+json']/text()").get()
        productjson = json.loads(responseJson)
        self.GetProductInfo(response)

    def GetName(self, response):
        color = self.GetSelectedColor(response)
        name = response.xpath("//h1[contains(@class,'x-product-title--text')]/text()").get()
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
