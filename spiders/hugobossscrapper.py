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


class HugoBossScrapper(Spider_BaseClass):
    Spider_BaseClass.cookiesDict = {"currency": "USD", "currencyOverride": "USD"}

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(HugoBossScrapper, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        return spider

    def GetProductUrls(self, homePageResponse):
        # ========== Category And Subcategory ========== #
        topCategoryNodes = homePageResponse.xpath(
            "//ul[@class='main-nav__gender']/li[a[contains(span/text(),'Men') or contains(span/text(),'Women')]]")
        for topCategoryNode in topCategoryNodes:
            topCategoryTitle = topCategoryNode.xpath("./a/span/text()").get().strip()
            # topCategorylink = topCategoryNode.xpath("./a/@href").get()
            # if not topCategorylink.startswith(store_url):
            #     topCategorylink = store_url.rstrip('/') + topCategorylink
            categoryNodes = topCategoryNode.xpath(
                "./div/ul/li[a[contains(text(),'Clothing')]]")
            for categoryNode in categoryNodes:
                categoryTitle = categoryNode.xpath("./a/text()").get().strip()
                # categorylink = categoryNode.xpath("./a/@href").get()
                # if not categorylink.startswith(store_url):
                #     categorylink = store_url.rstrip('/') + categorylink
                subCategoryNodes = categoryNode.xpath(
                    "./div//ul/li/a[contains(span/text(),'Suits') or contains(span/text(),'Dresses')]")
                for subCategoryNode in subCategoryNodes:
                    subCategoryTitle = subCategoryNode.xpath("./span/text()").get().strip()
                    subCategorylink = subCategoryNode.xpath("./@href").get()
                    if not subCategorylink.startswith(store_url):
                        subCategorylink = store_url.rstrip('/') + subCategorylink
                    category = topCategoryTitle + " " + categoryTitle + " " + subCategoryTitle
                    self.listing(subCategorylink, category)
        return Spider_BaseClass.AllProductUrls

    def listing(self, categorylink, category):
        categoryLinkResponse = requests.get(categorylink, stream=True)
        categoryLinkResponse = HtmlResponse(url=categorylink, body=categoryLinkResponse.text, encoding='utf-8')
        product_list = categoryLinkResponse.xpath(
            "//a[contains(@class,'product-tile__product-image')]/@href").extract()
        for productUrl in product_list:
            if not productUrl.startswith(store_url):
                productUrl = store_url.rstrip('/us/') + productUrl
            Spider_BaseClass.AllProductUrls.append(productUrl)
            siteMapCategory = str(Spider_BaseClass.ProductUrlsAndCategory.get(productUrl)).replace('None', '')
            if siteMapCategory:
                Spider_BaseClass.ProductUrlsAndCategory[productUrl] = siteMapCategory + " " + category
            else:
                Spider_BaseClass.ProductUrlsAndCategory[productUrl] = category
        try:
            nextPageUrl = categoryLinkResponse.xpath("//a[@title='Next']/@href").get()
            if not nextPageUrl.startswith(store_url):
                nextPageUrl = store_url.rstrip('/') + nextPageUrl
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
        if re.search('"availability":"', response.text):
            productAvailability = response.text.split('"availability":"')[1].split('"}}')[0].strip()
            if not 'InStock' in productAvailability or 'PreOrder' in productAvailability:
                return True
            else:
                return False

    def GetName(self, response):
        color = self.GetSelectedColor(response)
        name = str(response.xpath("//h1[@class='pdp-stage__header-title']/text()").get()).strip()
        if not color == '' and not re.search(color, name, re.I):
            name = name + " - " + color
        return name

    def GetSelectedColor(self, response):
        return response.xpath(
            "//a[contains(@class,'slide--color-selector') and contains(@data-selected,'true')]/span/text()").get()

    def GetPrice(self, response):
        orignalPrice = response.xpath("//div[@class='pdp-stage__pricing']/div/div/div/s/text()").get()
        if orignalPrice is not None:
            return float(str(orignalPrice.strip()).replace('$', '').replace(',', ''))
        else:
            regularPrice = response.xpath(
                "//div[@class='pdp-stage__pricing']/div/div/div/text()").get()
            return float(str(regularPrice.strip()).replace('$', '').replace(',', ''))

    def GetSalePrice(self, response):
        salePrice = response.xpath(
            "//div[@class='pdp-stage__pricing']/div/div/div[contains(@class,'price-value--sales')]/text()").get()
        if salePrice is not None:
            return float(str(salePrice.strip()).replace("$", "").replace(',', ''))
        else:
            return 0

    def GetBrand(self, response):
        return str(response.xpath("//div[contains(@class,'pdp-stage__logo')]/svg/title/text()").get()).strip()

    def GetImageUrl(self, response):
        imageUrls = []
        images = response.xpath(
            "//div[contains(@class,'pdp-stage__image-container-wrapper')]/section/figure/hug-adaptive-picture/img/@data-src").extract()
        if images:
            for image in images:
                imageUrls.append(str(image).replace('&wid={width}&qlt={quality}', '').replace('{quality}', '80'))
            return imageUrls
        else:
            raise NotImplementedError('NO Images Found')

    def GetDescription(self, response):
        detail = response.xpath("//div[@class='pdp-stage__accordion-description']/text()").get().strip()
        detailList = ' '.join(response.xpath(
            "//div[@class='pdp-stage__accordion-description']/following-sibling::text()").extract()).replace(
            '\n', '').strip()

        care = response.xpath("//div[contains(@id,'product-container-care')]/text()").get().strip()
        careList = ' '.join(response.xpath(
            "//div[contains(@id,'product-container-care')]/div/span/text()").extract()).replace(
            '\n', '').strip()
        return detail + " " + detailList + care + " " + careList

    def GetSizes(self, response):
        productSizes = []
        colorName = self.GetSelectedColor(response)
        sizeOptions = response.xpath(
            "//ul[contains(@class,'size-select__list')]/li/a[not(contains(@class,'unselectable'))]/span/text()").extract()
        gender = ProductFilters.objects.get(ProductUrl=GetterSetter.ProductUrl).ParentCategory.split(',')[0]
        for sizeName in sizeOptions:
            fitType = GetFitType(gender, str(sizeName).strip())
            available = True
            sizelist = str(colorName), str(sizeName).strip(), available, str(fitType), 0.0, 0.0
            productSizes.append(sizelist)
        return productSizes

    def GetCategory(self, response):
        siteMapCategory = str(Spider_BaseClass.ProductUrlsAndCategory.get(GetterSetter.ProductUrl)).replace('None', '')
        return siteMapCategory
