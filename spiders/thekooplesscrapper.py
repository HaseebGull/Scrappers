import sys
from pathlib import Path

DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(DIR.parent.parent.parent.parent))
__package__ = DIR.name

import django

django.setup()
from Magento import *
from scrapy import signals

store_url = sys.argv[4]


class TheKooplesScrapper(magento):
    # Spider_BaseClass.cookiesDict = {"currency": "USD", "currencyOverride": "USD"}

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(TheKooplesScrapper, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        return spider

    Spider_BaseClass.sampleUrl = store_url + 'sitemap/'

    def GetProductUrls(self, homePageResponse):
        # ========== Category And Subcategory ========== #
        topCategoryNodes = homePageResponse.xpath(
            "//div[@class='xsitemap-categories']/ul/li[a[text()='Women' or text()='Men']]")
        for topCategoryNode in topCategoryNodes:
            topCategoryTitle = topCategoryNode.xpath("./a/text()").get().strip()
            # topCategorylink = topCategoryNode.xpath("./a/@href").get()
            # if not topCategorylink.startswith(store_url):
            #     topCategorylink = store_url.rstrip('/') + topCategorylink
            categoryNodes = topCategoryNode.xpath(
                "./ul/li[a[contains(text(),'New') or contains(text(),'Clothing') or contains(text(),'Online') or contains(text(),'Sale')]]")
            for categoryNode in categoryNodes:
                categoryTitle = categoryNode.xpath("./a/text()").get().strip()
                # categorylink = categoryNode.xpath("./a/@href").get()
                # if not categorylink.startswith(store_url):
                #     categorylink = store_url.rstrip('/') + categorylink
                subCategoryNodes = categoryNode.xpath(
                    "./ul/li/a[contains(text(),'Dress') or contains(text(),'Suit') or contains(text(),'Jumpsuits')]")
                for subCategoryNode in subCategoryNodes:
                    subCategoryTitle = subCategoryNode.xpath("./text()").get().strip()
                    subCategorylink = subCategoryNode.xpath("./@href").get()
                    if not subCategorylink.startswith(store_url):
                        subCategorylink = store_url.rstrip('/') + subCategorylink
                    category = topCategoryTitle + " " + categoryTitle + " " + subCategoryTitle
                    self.listing(subCategorylink, category)
        return Spider_BaseClass.AllProductUrls

    def listing(self, categorylink, category):
        listingJsonStr = ''
        categoryLinkResponse = requests.get(categorylink, stream=True)
        categoryLinkResponse = HtmlResponse(url=categorylink, body=categoryLinkResponse.text, encoding='utf-8')

        if re.search('var reactProps               = {', categoryLinkResponse.text):
            listingJsonStr = '{' + str(
                categoryLinkResponse.text.split('var reactProps               = {')[1].split(
                    'reactPropsCategoriesList')[0]).rstrip().rstrip(',')

        productListingJson = json.loads(listingJsonStr)

        totalProducts = productListingJson['pagination']['totalArticles']
        totalPages = productListingJson['pagination']['totalPage']
        pageNo = productListingJson['pagination']['currentPage']
        if totalProducts % 36 == 0:
            totalPages = totalProducts / 36
        else:
            totalPages = totalProducts / 36 + 1
        while pageNo <= totalPages:
            pageNo += 1
            for apiproducturl in productListingJson['products']:
                productUrl = apiproducturl['url']
                if not productUrl.startswith(store_url):
                    productUrl = store_url.rstrip('/') + productUrl
                Spider_BaseClass.AllProductUrls.append(productUrl)
                siteMapCategory = str(Spider_BaseClass.ProductUrlsAndCategory.get(productUrl)).replace('None', '')
                if siteMapCategory:
                    Spider_BaseClass.ProductUrlsAndCategory[productUrl] = siteMapCategory + " " + category
                else:
                    Spider_BaseClass.ProductUrlsAndCategory[productUrl] = category
            try:
                nextpageUrl = categorylink + '?p=' + str(pageNo) + ''
                categoryLinkResponse = requests.get(url=nextpageUrl)
                if re.search('var reactProps               = {', categoryLinkResponse.text):
                    listingJsonStr = '{' + str(
                        categoryLinkResponse.text.split('var reactProps               = {')[1].split(
                            'reactPropsCategoriesList')[0]).rstrip().rstrip(',')
                productListingJson = json.loads(listingJsonStr)
            except:
                pass

    def GetProducts(self, response):
        ignorProduct = self.IgnoreProduct(response)
        if ignorProduct == True:
            self.ProductIsOutofStock(GetterSetter.ProductUrl)
        else:
            jsonStr = self.SetProductJson(response.text)
            if jsonStr != '':
                magento.productJson = json.loads(jsonStr)
            self.GetProductInfo(response)

    def SetProductJson(self, response):
        if re.search('var reactProps               = {', response):
            listingJsonStr = '{' + str(
                response.split('var reactProps               = {')[1].split(',"categoryLevel"')[0]) + '}'.strip()
            return listingJsonStr
        return ''

    def GetName(self, response):
        color = self.GetSelectedColor(response)
        name = magento.productJson['product']['name']
        if not color == '' and not re.search(color, name, re.I):
            name = name + " - " + color
        return name

    def GetSelectedColor(self, response):
        color = magento.productJson['product']['colorCode']
        return color

    def GetPrice(self, response):
        orignalPrice = magento.productJson['product']['prices']['old']
        return orignalPrice

    def GetSalePrice(self, response):
        salePrice = magento.productJson['product']['prices']['final']
        return salePrice

    def GetBrand(self, response):
        return magento.productJson['product']['brand']

    def GetImageUrl(self, response):
        imageUrls = []
        images = magento.productJson['product']['assets']
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
        sizeOptions = magento.productJson['product']['simples']
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
