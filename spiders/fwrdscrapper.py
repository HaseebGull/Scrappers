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


class FwrdScrapper(Spider_BaseClass):
    Spider_BaseClass.cookiesDict = {"currency": "USD", "currencyOverride": "USD"}

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(FwrdScrapper, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        return spider

    def GetProductUrls(self, homePageResponse):
        # ========== Category And Subcategory ==========#
        genderNodes = homePageResponse.xpath(
            "//ul[@class='ui-list']/li/a[contains(text(),'mens') or contains(text(),'Mens')]")
        for genderNode in genderNodes:
            genderTitle = genderNode.xpath("./text()").get().strip()
            genderlink = genderNode.xpath("./@href").get()
            if not genderlink.startswith(store_url):
                genderlink = store_url.rstrip('/') + genderlink
            genderLinkResponse = requests.get(genderlink, stream=True)
            genderLinkResponse = HtmlResponse(url=genderlink, body=genderLinkResponse.text, encoding='utf-8')

            topCategoryNodes = genderLinkResponse.xpath(
                "//ul[@class='nav-primary__list']/li/a[contains(text(),'clothing') or contains(text(),'sale')]")
            for topCategoryNode in topCategoryNodes:
                topCategoryTitle = topCategoryNode.xpath("./text()").get().strip()
                topCategorylink = topCategoryNode.xpath("./@href").get()
                if not topCategorylink.startswith(store_url):
                    topCategorylink = store_url.rstrip('/') + topCategorylink
                topCategoryLinkResponse = requests.get(topCategorylink, stream=True)
                topCategoryLinkResponse = HtmlResponse(url=topCategorylink, body=topCategoryLinkResponse.text,
                                                       encoding='utf-8')
                categoryNodes = topCategoryLinkResponse.xpath(
                    "//div[@class='plp__sidebar']/div/h2[contains(text(),'Category')]/following-sibling::ul/li/a[contains(text(),'Dress') or contains(text(),'Jumpsuits') or contains(text(),'Suits')]")
                for categoryNode in categoryNodes:
                    categoryTitle = categoryNode.xpath("./text()").get().strip()
                    categorylink = categoryNode.xpath("./@href").get()
                    if not categorylink.startswith(store_url):
                        categorylink = store_url.rstrip('/') + categorylink

                    categoryLinkResponse = requests.get(categorylink, stream=True)
                    categoryLinkResponse = HtmlResponse(url=categorylink, body=categoryLinkResponse.text,
                                                        encoding='utf-8')
                    if topCategoryTitle == 'sale':
                        category = genderTitle + " " + topCategoryTitle + " " + categoryTitle
                        self.listing(categorylink, category)
                    else:
                        subCategoryNodes = categoryLinkResponse.xpath(
                            "//ul[@class='nav-list']/li/a[not(contains(text(),'View all')) and not(contains(text(),'All Sale Items'))]")
                        if not subCategoryNodes:
                            category = genderTitle + " " + topCategoryTitle + " " + categoryTitle
                            self.listing(categorylink, category)
                        for subCategoryNode in subCategoryNodes:
                            subCategoryTitle = subCategoryNode.xpath("./text()").get().strip()
                            subCategorylink = subCategoryNode.xpath("./@href").get()
                            if not subCategorylink.startswith(store_url):
                                subCategorylink = store_url.rstrip('/') + subCategorylink
                            category = genderTitle + " " + topCategoryTitle + " " + categoryTitle + " " + subCategoryTitle
                            self.listing(subCategorylink, category)
        return Spider_BaseClass.AllProductUrls

    def listing(self, categorylink, category):
        categoryLinkResponse = requests.get(categorylink, stream=True)
        categoryLinkResponse = HtmlResponse(url=categorylink, body=categoryLinkResponse.text, encoding='utf-8')
        product_list = categoryLinkResponse.xpath(
            "//ul[contains(@class,'product-grids')]/li/a[contains(@class,'product-grids__link product')]/@href").extract()
        for productUrl in product_list:
            if not productUrl.startswith(store_url):
                productUrl = store_url.rstrip('/') + productUrl
            if re.search('https://', productUrl) and re.search('\?', productUrl):
                productUrl = 'https://' + productUrl.split('https://')[1].split('?')[0].strip()
            Spider_BaseClass.AllProductUrls.append(productUrl)
            siteMapCategory = str(Spider_BaseClass.ProductUrlsAndCategory.get(productUrl)).replace('None', '')
            if siteMapCategory:
                Spider_BaseClass.ProductUrlsAndCategory[productUrl] = siteMapCategory + " " + category
            else:
                Spider_BaseClass.ProductUrlsAndCategory[productUrl] = category
        try:
            nextPageNo = categoryLinkResponse.xpath(
                "//a[@rel='next' and contains(@id,'tr-pagination__controls--next')]/@data-page-num").get()
            if nextPageNo:
                if re.search('pageNum=', categorylink):
                    categorylink = categorylink.split('pageNum')[0].rstrip('? | &')
                if re.search('\?', categorylink):
                    nextPageUrl = categorylink + '&pageNum=' + str(nextPageNo) + ''
                else:
                    nextPageUrl = categorylink + '?pageNum=' + str(nextPageNo) + ''
                self.listing(nextPageUrl, category)
        except:
            pass

    def GetProducts(self, response):
        global productjson
        ignorProduct = self.IgnoreProduct(response)
        if ignorProduct == True:
            self.ProductIsOutofStock(GetterSetter.ProductUrl)
        else:
            self.GetProductInfo(response)

    def IgnoreProduct(self, response):
        outOfStock = response.xpath("//input[@type='button' and contains(@value,'notify me')]")
        if outOfStock:
            return True
        else:
            return False

    def GetName(self, response):
        color = self.GetSelectedColor(response)
        name = str(response.xpath("//h1[contains(@class,'u-margin-b--md')]/div/text()").get()).strip()
        if not color == '' and not re.search(color, name, re.I):
            name = name + " - " + color
        return name

    def GetSelectedColor(self, response):
        try:
            return response.xpath(
                "//div[contains(@id,'pdp-color') and contains(div/span/text(),'Color')]/div/span[contains(@id,'pdp-color-selected')]/text()").get().strip()
        except:
            return response.xpath(
                "//div[contains(@id,'pdp-color') and contains(div/span/text(),'Color')]/div/span[contains(@class,'pdp__color-option')]/text()").get().strip()

    def GetPrice(self, response):
        orignalPrice = response.xpath(
            "//div[@class='price price--lg']/span[contains(@class,'price__retail')]/text()").get()
        if orignalPrice != None:
            return float(str(orignalPrice).replace('$', '').replace(',', ''))
        else:
            regularPrice = response.xpath(
                "//div[contains(@class,'u-margin-b--md')]//s[@class='price__retail']/span/following-sibling::text()").get()
            return float(str(regularPrice).replace('$', '').replace(',', ''))

    def GetSalePrice(self, response):
        salePrice = response.xpath(
            "//div[@class='price price--lg price--on-sale']/span/text()").get()
        if salePrice != None:
            return float(str(salePrice).replace("$", "").replace(',', ''))
        else:
            return 0

    def GetBrand(self, response):
        return str(response.xpath("//a[contains(@class,'pdp__brand-title')]/text()").get()).strip()

    def GetImageUrl(self, response):
        imageUrls = []
        images = response.xpath("//div[contains(@class,'js-slides-slick')]/div/@data-zoom-img").extract()
        if images:
            for image in images:
                imageUrls.append(image)
            return imageUrls
        else:
            raise NotImplementedError('NO Images Found')

    def GetDescription(self, response):
        return ' '.join(response.xpath("//div[@id='pdp-details']/ul/li/text()").extract()).replace(
            '\n', '').strip()

    def GetSizes(self, response):
        productSizes = []
        colorName = self.GetSelectedColor(response)
        sizeOptions = response.xpath(
            "//div[contains(@id,'pdp-sizes')]/div[contains(@class,'u-flex-wrap')]/div/input[not(@disabled)]/following-sibling::label/text()").extract()
        gender = ProductFilters.objects.get(ProductUrl=GetterSetter.ProductUrl).ParentCategory.split(',')[0]
        for sizeName in sizeOptions:
            fitType = GetFitType(gender, sizeName)
            available = True
            sizelist = str(colorName), str(sizeName), available, str(fitType), 0.0, 0.0
            productSizes.append(sizelist)
        return productSizes

    def GetCategory(self, response):
        siteMapCategory = str(Spider_BaseClass.ProductUrlsAndCategory.get(GetterSetter.ProductUrl)).replace('None', '')
        return siteMapCategory
