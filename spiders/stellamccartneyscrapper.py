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


class StellaMcCartneyScrapper(Spider_BaseClass):
    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(StellaMcCartneyScrapper, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        return spider

    def GetProductUrls(self, homePageResponse):
        # ========== Category And Subcategory ==========#
        topCategoryNodes = homePageResponse.xpath(
            "//div[contains(@class,'main-navigation__menu-col')][1]/ul/li[a[contains(span/text(),'Women') or contains(span/text(),'Kids')]]")
        for topCategoryNode in topCategoryNodes:
            topCategoryTitle = topCategoryNode.xpath("./a/span/text()").get().strip()
            topCategorylink = topCategoryNode.xpath("./a/@href").get()
            if not topCategorylink.startswith(store_url):
                topCategorylink = store_url.rstrip('/') + topCategorylink
            categoryNodes = topCategoryNode.xpath(
                "./ul/li[a[contains(span/text(),'Ready to Wear') or contains(span/text(),'Girl') or contains(span/text(),'Boy') or contains(span/text(),'Baby')]]")
            for categoryNode in categoryNodes:
                categoryTitle = categoryNode.xpath("./a/span/text()").get().strip()
                categorylink = categoryNode.xpath("./a/@href").get()
                if not categorylink.startswith(store_url):
                    categorylink = store_url.rstrip('/') + categorylink
                subCategoryNodes = categoryNode.xpath(
                    "./ul/li/a[contains(span/text(),'Dresses') or contains(span/text(),'Jumpsuits') or contains(span/text(),'Rompers') or contains(span/text(),'New')]")
                for subCategoryNode in subCategoryNodes:
                    subCategoryTitle = subCategoryNode.xpath("./span/text()").get().strip()
                    subCategorylink = subCategoryNode.xpath("./@href").get()
                    if not subCategorylink.startswith(store_url):
                        subCategorylink = store_url.rstrip('/') + subCategorylink
                    if re.search('\?', subCategorylink):
                        subCategorylink = 'https' + subCategorylink.split('https' or 'http')[1].split('?')[0].strip()
                    if categoryTitle == 'Boys' and subCategoryTitle == 'New Arrivals':
                        continue
                    else:
                        category = topCategoryTitle + " " + categoryTitle + " " + subCategoryTitle
                        self.listing(subCategorylink, category)
        return Spider_BaseClass.AllProductUrls

    def listing(self, subCategorylink, category):
        subCategoryLinkResponse = requests.get(subCategorylink)
        subCategoryLinkResponse = HtmlResponse(url=subCategorylink, body=subCategoryLinkResponse.text, encoding='utf-8')
        product_list = subCategoryLinkResponse.xpath(
            "//div[@class='product-tile__body--link']/a/@href").extract()
        for productUrl in product_list:
            if not productUrl.startswith(store_url):
                productUrl = store_url.rstrip('/') + productUrl
            Spider_BaseClass.AllProductUrls.append(productUrl)
            siteMapCategory = str(Spider_BaseClass.ProductUrlsAndCategory.get(productUrl)).replace('None', '')
            if siteMapCategory:
                Spider_BaseClass.ProductUrlsAndCategory[productUrl] = siteMapCategory + " " + category
            else:
                Spider_BaseClass.ProductUrlsAndCategory[productUrl] = category
        try:
            nextPageUrl = subCategoryLinkResponse.xpath("//div[@class='show-more']/div/button/@data-url").extract()[0]
            if not nextPageUrl.startswith(store_url):
                nextPageUrl = store_url.rstrip('/') + nextPageUrl
            self.listing(nextPageUrl, category)
        except:
            pass

    def GetProducts(self, response):
        ignorProduct = self.IgnoreProduct(response)
        if ignorProduct == True:
            self.ProductIsOutofStock(GetterSetter.ProductUrl)
        else:
            global productjson
            responseJson = response.xpath("//script[@type='application/ld+json']/text()").get()
            productjson = json.loads(responseJson)
            categoryAndName = self.GetCategory(response) + " " + self.GetName(response)
            if (re.search(r'\b' + 'New Arrivals' + r'\b', categoryAndName, re.IGNORECASE)) and not \
                    re.search(
                        r'\b((shirt(dress?)|jump(suit?)|dress|body set|dungaree|romper|gown|suit|caftan)(s|es)?)\b',
                        categoryAndName,
                        re.IGNORECASE):
                print('Skipping Non Dress Product')
                self.ProductIsOutofStock(GetterSetter.ProductUrl)
            else:
                self.GetProductInfo(response)

    def GetName(self, response):
        color = self.GetSelectedColor(response)
        name = response.xpath("//h1[contains(@class,'product-name')]/text()").get()
        if not color == '' and not re.search(color, name):
            name = name + " - " + color
        return name

    def GetSelectedColor(self, response):
        return response.xpath(
            "(//span[contains(@class,'color')])[1]/span[contains(@class,'attribute__label-select')]/text()").get()

    def GetPrice(self, response):
        orignalPrice = response.xpath(
            "//div[contains(@class,'prices')]/div[@class='price']/span/del/span[contains(@class,'strike-through')]/span/@content").get()
        if orignalPrice != None:
            return float(str(orignalPrice).replace('$', '').replace(',', ''))
        else:
            regularPrice = response.xpath(
                "//span[@class='sales']/span/text()").get()
            return float(str(regularPrice).replace('$', '').replace(',', ''))

    def GetSalePrice(self, response):
        salePrice = response.xpath(
            "//span[@class='sales']/span/text()").get()
        if salePrice != None:
            return float(str(salePrice).replace("$", "").replace(',', ''))
        else:
            return 0

    def GetBrand(self, response):
        return productjson['brand']['name']

    def GetImageUrl(self, response):
        imageUrls = []
        images = response.xpath(
            "//div[@class='primary-images']/div/div[@class='carousel-inner']/a/@data-zoom-hires").extract()
        for image in images:
            imageUrls.append(image)
        return imageUrls

    def GetDescription(self, response):
        detail = response.xpath("(//p[contains(@class,'description-and-detail__paragraph')])[1]/text()").get()
        if not detail:
            detail = ''
        detailList = response.xpath("//div[@class='content-body']/ul/li/text()").extract()
        description = ' '.join(detailList)
        return detail + " " + description

    def GetSizes(self, response):
        productSizes = []
        colorName = self.GetSelectedColor(response)
        gender = ProductFilters.objects.get(ProductUrl=GetterSetter.ProductUrl).ParentCategory.split(',')[0]
        sizeOptions = response.xpath(
            "(//div[@data-attr='size'])[1]/div[@class='attribute ']/div[contains(@class,'attribute__values')]/button[contains(@class,'selectable')]/span[contains(@class,'selectable') and not(contains(@class,'unselectable'))]/@data-attr-value").extract()
        for sizeName in sizeOptions:
            available = True
            fitType = GetFitType(gender, str(sizeName).strip())
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
        return siteMapCategory
