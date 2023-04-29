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


class HallensteinBrothersScrapper(Spider_BaseClass):
    Spider_BaseClass.cookiesDict = {
        "Cookie": "PHPSESSID=bb6efadbbcb95ac12d07d8a31fc8c937; pscartkey=2753f75712ae4c29f55e7e630a495dcd; bp_welcome=6242cb5d298cb; landedpage=%2Fsuits%2Fsuit-bundles; _dd_s=logs=1&id=59a7a22e-b15d-4403-922e-67afb256fa3e&created=1648544607410&expire=1648545684985; _gcl_au=1.1.1258053889.1648544608; scarab.visitor=%222D5EA60752A01D3F%22; _ga=GA1.2.1427276761.1648544610; _gid=GA1.2.2085368114.1648544610; _fbp=fb.1.1648544611095.764006539; _clck=1r6o6p4|1|f06|0; _hjSessionUser_2456165=eyJpZCI6IjFlOTgzYjUwLWNjZjEtNTQxNC04ZDdhLWM0ODUyMTNmMGFiMyIsImNyZWF0ZWQiOjE2NDg1NDQ2MTE1NjAsImV4aXN0aW5nIjp0cnVlfQ==; _hjFirstSeen=1; _hjIncludedInSessionSample=0; _hjSession_2456165=eyJpZCI6IjYxOWUyNjIwLWJhYTYtNGZkOS1hMjUwLTFmNjFmNzUyZGQ1NyIsImNyZWF0ZWQiOjE2NDg1NDQ2MTE4NjcsImluU2FtcGxlIjpmYWxzZX0=; _hjAbsoluteSessionInProgress=1; _clsk=111iy1q|1648544621177|2|1|l.clarity.ms/collect; __qca=P0-831756105-1648544611740; psuserurilocale=NZ; show_bp_welcome=1648544626; candid_userid=539639db-79b4-41ca-b657-6804842cd545; _uetsid=195e2cd0af3f11ecb8cc051d179f0924; _uetvid=195e4040af3f11ec8c70331142b6acb4; _hjDonePolls=792821"}

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(HallensteinBrothersScrapper, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        return spider

    def GetProductUrls(self, homePageResponse):
        # ========== Category And Subcategory ========== #
        topCategoryNodes = homePageResponse.xpath(
            "//ul[contains(@class,'site-nav-primary')]/li[a[contains(text(),'Clothing') or contains(text(),'Suits')]]")
        for topCategoryNode in topCategoryNodes:
            topCategoryTitle = topCategoryNode.xpath("./a/text()").get().strip()
            # topCategorylink = topCategoryNode.xpath("./a/@href").get()
            # if not topCategorylink.startswith(store_url):
            #     topCategorylink = store_url.rstrip('/') + topCategorylink
            categoryNodes = topCategoryNode.xpath(
                "./div/div/div/div/ul/li[a[not(contains(text(),'T Shirts'))and contains(text(),'Shirts') or contains(text(),'Bundle') "
                "or contains(text(),'Suit Jacket') or contains(text(),'Suit ') or contains(text(),'Pants') and not(contains(text(),'Track'))]]")
            for categoryNode in categoryNodes:
                categoryTitle = categoryNode.xpath("./a/text()").get().strip()
                categorylink = categoryNode.xpath("./a/@href").get()
                if not categorylink.startswith(store_url):
                    categorylink = store_url.rstrip('/') + categorylink
                subCategoryNodes = categoryNode.xpath(
                    "./div/ul/li/a[contains(text(),'Dress') or contains(text(),'Jacket') or contains(text(),'Waistcoats') or contains(text(),'Business')]")
                if not subCategoryNodes:
                    categorylink = str(categorylink).replace('/us/us', '/us')
                    category = "Men " + topCategoryTitle + " " + categoryTitle
                    print(categorylink)
                    print(category)
                    self.listing(categorylink, category)
                for subCategoryNode in subCategoryNodes:
                    subCategoryTitle = subCategoryNode.xpath("./text()").get().strip()
                    subCategorylink = subCategoryNode.xpath("./@href").get()
                    if not subCategorylink.startswith(store_url):
                        subCategorylink = store_url.rstrip('/') + subCategorylink
                    subCategorylink = str(subCategorylink).replace('/us/us', '/us')
                    category = "Men " + topCategoryTitle + " " + categoryTitle + " " + subCategoryTitle
                    self.listing(subCategorylink, category)
        return Spider_BaseClass.AllProductUrls

    def listing(self, categorylink, category):
        listingJsonStr = ''
        categoryLinkResponse = requests.get(categorylink, cookies=Spider_BaseClass.cookiesDict, stream=True)
        categoryLinkResponse = HtmlResponse(url=categorylink, body=categoryLinkResponse.text, encoding='utf-8')

        if re.search('window.category =', categoryLinkResponse.text):
            listingJsonStr = str(
                categoryLinkResponse.text.split('window.category =')[1].split('window.isvintage = 0;')[
                    0].rstrip().strip(';'))
        productListingJson = json.loads(listingJsonStr)
        totalProducts = productListingJson['totalitems']
        totalPages = productListingJson['totalpages']
        pageNo = productListingJson['currentpage']
        if totalProducts % 24 == 0:
            totalPages = totalProducts / 24
        else:
            totalPages = totalProducts / 24 + 1
        while pageNo <= totalPages:
            pageNo += 1
            for apiproducturl in productListingJson['items']:
                productUrl = apiproducturl['stylecolour']['urlkey']
                if not productUrl.startswith(store_url):
                    productUrl = store_url + productUrl
                print(productUrl)
                Spider_BaseClass.AllProductUrls.append(productUrl)
                siteMapCategory = str(Spider_BaseClass.ProductUrlsAndCategory.get(productUrl)).replace('None', '')
                if siteMapCategory:
                    Spider_BaseClass.ProductUrlsAndCategory[productUrl] = siteMapCategory + " " + category
                else:
                    Spider_BaseClass.ProductUrlsAndCategory[productUrl] = category
            try:
                nextpageUrl = categorylink + '?p=' + str(pageNo) + ''
                categoryLinkResponse = requests.get(url=nextpageUrl)
                if re.search('window.category =', categoryLinkResponse.text):
                    listingJsonStr = str(
                        categoryLinkResponse.text.split('window.category =')[1].split('window.isvintage = 0;')[
                            0].rstrip().strip(';'))
                productListingJson = json.loads(listingJsonStr)
            except:
                pass

    def GetProducts(self, response):
        global productJson
        ignorProduct = self.IgnoreProduct(response)
        if ignorProduct == True:
            self.ProductIsOutofStock(GetterSetter.ProductUrl)
        else:
            jsonStr = self.SetProductJson(response.text)
            if jsonStr != '':
                productJson = json.loads(jsonStr)
            self.GetProductInfo(response)

    def SetProductJson(self, response):
        if re.search('var reactProps               = {', response):
            listingJsonStr = '{' + str(
                response.split('var reactProps               = {')[1].split(',"categoryLevel"')[0]) + '}'.strip()
            return listingJsonStr
        return ''

    def GetName(self, response):
        color = self.GetSelectedColor(response)
        name = productJson['product']['name']
        if not color == '' and not re.search(color, name, re.I):
            name = name + " - " + color
        return name

    def GetSelectedColor(self, response):
        color = productJson['product']['colorCode']
        return color

    def GetPrice(self, response):
        orignalPrice = productJson['product']['prices']['old']
        return orignalPrice

    def GetSalePrice(self, response):
        salePrice = productJson['product']['prices']['final']
        return salePrice

    def GetBrand(self, response):
        return productJson['product']['brand']

    def GetImageUrl(self, response):
        imageUrls = []
        images = productJson['product']['assets']
        if images:
            for image in images:
                if image['urls'] != {}:
                    imageUrls.append(image['urls']['big'])
                if image['type'] == 'video':
                    imageUrls.append(image['videoUrl'])
            return imageUrls
        else:
            raise NotImplementedError('NO Images Found')

    def GetDescription(self, response):
        description = ' '.join(
            response.xpath(
                "//div[contains(@class,'productPagePortal ')]/div[h2[contains(text(),'Description')]]/p/ul/li/text()").extract()).replace(
            '\n', '').strip()
        if not description:
            description = response.xpath("//meta[@property='og:description']/@content").get()
        fabricAndCare = ' '.join(
            response.xpath(
                "//div[contains(@class,'productPagePortal ')]/div[h2[contains(text(),'Care')]]/p/text()").extract()).replace(
            '\n', '').strip()
        return description + " " + fabricAndCare

    def GetSizes(self, response):
        productSizes = []
        colorName = self.GetSelectedColor(response)
        sizeOptions = productJson['product']['simples']
        gender = ProductFilters.objects.get(ProductUrl=GetterSetter.ProductUrl).ParentCategory.split(',')[0]
        for sizeOption in sizeOptions:
            if sizeOption['isInStock'] == True:
                sizeName = sizeOption['size']['label']
                fitType = GetFitType(gender, sizeName)
                available = True
                sizelist = str(colorName), str(sizeName), available, str(fitType), 0.0, 0.0
                productSizes.append(sizelist)
        return productSizes

    def GetCategory(self, response):
        siteMapCategory = str(Spider_BaseClass.ProductUrlsAndCategory.get(GetterSetter.ProductUrl)).replace('None', '')
        return siteMapCategory.strip()
