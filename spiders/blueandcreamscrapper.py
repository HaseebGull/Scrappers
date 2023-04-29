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


class BlueandcreamScrapper(Spider_BaseClass):
    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(BlueandcreamScrapper, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        return spider

    def GetProductUrls(self, homePageResponse):
        # ========== Category And Subcategory ==========#
        topCategoryNodes = homePageResponse.xpath(
            "//div[@class='t-main-category-selection']/a[contains(text(),'Women')]")
        for topCategoryNode in topCategoryNodes:
            topCategoryTitle = topCategoryNode.xpath("./text()").get().strip()
            categoryNodes = homePageResponse.xpath(
                "//div[@id='mega_menu']/div[contains(span/a/text(),'Clothing') or contains(span/a/text(),'New') or contains(span/a/text(),'Sale')]")
            for categoryNode in categoryNodes:
                categoryTitle = categoryNode.xpath("./span/a/text()").get().strip()
                categorylink = categoryNode.xpath("./span/a/@href").get()
                if not categorylink.startswith(store_url):
                    categorylink = store_url.rstrip('/') + categorylink
                subCategoryNodes = categoryNode.xpath(
                    ".//div[@class='t-mm-link']/a[contains(text(),'Dresses') or contains(text(),'Jumpsuits')]")
                if not subCategoryNodes:
                    category = topCategoryTitle + " " + categoryTitle
                    print(category)
                    self.listing(categorylink, category)
                else:
                    for subCategoryNode in subCategoryNodes:
                        subCategoryTitle = subCategoryNode.xpath("./text()").get().strip()
                        subCategorylink = subCategoryNode.xpath("./@href").get()
                        if not subCategorylink.startswith(store_url):
                            subCategorylink = store_url.rstrip('/') + subCategorylink
                        category = topCategoryTitle + " " + categoryTitle + " " + subCategoryTitle
                        print(category)
                        self.listing(subCategorylink, category)
        return Spider_BaseClass.AllProductUrls

    def listing(self, categorylink, category):
        categoryCode = ''
        CategoryLinkResponse = requests.get(categorylink)
        CategoryLinkResponse = HtmlResponse(url=categorylink, body=CategoryLinkResponse.text, encoding='utf-8')
        if re.search("Category_Code = '", CategoryLinkResponse.text):
            categoryCode = CategoryLinkResponse.text.split("Category_Code = '")[1].split("';")[0].strip()
        apiUrl = 'https://43gpw0.a.searchspring.io/api/search/search.json?ajaxCatalog=v3&resultsFormat=native&siteId=43gpw0&domain=https://www.blueandcream.com/category/' + str(
            categoryCode) + '.html&bgfilter.catcode=' + str(categoryCode) + '&q=&page=1'
        apiresponse = requests.get(url=apiUrl, timeout=6000)
        apiresponseJson = json.loads(apiresponse.content)
        totalPage = apiresponseJson['pagination']['totalPages']
        pageNo = 2
        self.GetUrls(apiresponseJson, category)
        while pageNo <= totalPage:
            nextPageUrl = 'https://43gpw0.a.searchspring.io/api/search/search.json?ajaxCatalog=v3&resultsFormat=native&siteId=43gpw0&domain=https://www.blueandcream.com/category/' + str(
                categoryCode) + '.html&bgfilter.catcode=' + str(categoryCode) + '&q=&page=' + str(
                pageNo) + ''
            apiresponse = requests.get(url=nextPageUrl, timeout=6000)
            apiresponseJson = json.loads(apiresponse.content)
            self.GetUrls(apiresponseJson, category)
            pageNo = pageNo + 1

    def GetUrls(self, datJson, category):
        for proNode in datJson['results']:
            catJsosn = proNode['category']
            jsonCategories = '$'.join(map(str, catJsosn))

            productUrl = proNode['url']
            if not productUrl.startswith(store_url):
                productUrl = store_url.rstrip('/') + productUrl
            Spider_BaseClass.AllProductUrls.append(productUrl)

            siteMapCategory = str(Spider_BaseClass.ProductUrlsAndCategory.get(productUrl)).replace('None', '')
            if siteMapCategory:
                Spider_BaseClass.ProductUrlsAndCategory[
                    productUrl] = siteMapCategory + " " + category + " " + jsonCategories
            else:
                Spider_BaseClass.ProductUrlsAndCategory[productUrl] = category + " " + jsonCategories

    def GetProducts(self, response):
        global productjson
        ignorProduct = self.IgnoreProduct(response)
        if ignorProduct == True:
            self.ProductIsOutofStock(GetterSetter.ProductUrl)
        else:
            responseJson = response.xpath("//script[@type='application/ld+json']/text()").get()
            productjson = json.loads(responseJson)
            categoryAndName = self.GetCategory(response) + " " + self.GetName(response)
            if (re.search('sale', categoryAndName, re.IGNORECASE) or
                re.search('New', categoryAndName, re.IGNORECASE) or
                re.search('new arrival', categoryAndName, re.IGNORECASE)) and not re.search(
                r'\b((shirt(dress?)|jump(suit?)|dress|gown|suit|caftan)(s|es)?)\b', categoryAndName,
                re.IGNORECASE):
                print('Skipping Non Dress Product')
                self.ProductIsOutofStock(GetterSetter.ProductUrl)
            else:
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
                imageurl = "https://www.blueandcream.com/mm5/" + str(image['image_data'][0]).replace(" ", '%20')
                imageUrls.append(imageurl)
        return imageUrls

    def GetDescription(self, response):
        return productjson['description']

    def GetSizes(self, response):
        productSizes = []
        sku = productjson['sku']
        colorName = self.GetSelectedColor(response)
        sizeOptions = response.xpath("//input[@data-attribute='size' or @data-attribute='Size']/@value").extract()
        gender = ProductFilters.objects.get(ProductUrl=GetterSetter.ProductUrl).ParentCategory.split(',')[0]
        for sizeName in sizeOptions:
            prodId = sku + '_' + sizeName
            for sizeValue in productjson['offers']:
                if sizeValue['sku'] == prodId:
                    if 'InStock' in sizeValue['availability']:
                        available = True
                        fitType = GetFitType(gender, sizeName)
                        sizelist = str(colorName), str(sizeName), available, str(fitType), 0.0, 0.0
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
        siteMapCategory = str(Spider_BaseClass.ProductUrlsAndCategory.get(GetterSetter.ProductUrl)).replace('None', '')
        return siteMapCategory.strip()
