import sys
from pathlib import Path

from SiteSizesDict import *

DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(DIR.parent.parent.parent.parent))
__package__ = DIR.name

import django

django.setup()
from BaseClass import *
from scrapy import signals

store_url = sys.argv[4]


class MrPorterScrapper(Spider_BaseClass):
    Spider_BaseClass.cookies_dict = {"country_iso": "US", "lang_iso": "en"}

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(MrPorterScrapper, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        return spider

    def GetProductUrls(self, homePageResponse):
        # ========== Category And Subcategory ==========#
        topCategoryNodes = homePageResponse.xpath(
            "//ul[contains(@class,'Nav2__list')]/li/div[a[contains(span/text(),'Clothing')]]")
        for topCategoryNode in topCategoryNodes:
            topCategoryTitle = topCategoryNode.xpath("./a/span/text()").get().strip()
            categoryNodes = topCategoryNode.xpath(
                ".//div[@class='gc']/ul/li[contains(@class,'ui-list__item')]/a[contains(text(),'Dress') or contains(text(),'Jumpsuits') or contains(text(),'Rompers')]")
            for categoryNode in categoryNodes:
                categoryTitle = categoryNode.xpath("./text()").get().strip()
                categorylink = categoryNode.xpath("./@href").get()
                if not categorylink.startswith(store_url):
                    categorylink = store_url.rstrip('/') + categorylink
                print("CATEGORY  :", categoryTitle, "CATEGORY LINK  :", categorylink)

                categoryLinkResponse = requests.get(categorylink, stream=True)
                categoryLinkResponse = HtmlResponse(url=categorylink, body=categoryLinkResponse.text, encoding='utf-8')

                if topCategoryTitle == 'Sale' and categoryTitle == "Dresses":
                    subCategoryNodes = categoryLinkResponse.xpath(
                        "//div[contains(@class,'sidebar--categories')]/div/aside/h2/following-sibling::ul/li/a[contains(text(),'Dress') or contains(text(),'Jumpsuits') or contains(text(),'Rompers')]")
                    for subCategoryNode in subCategoryNodes:
                        subCategoryTitle = subCategoryNode.xpath("./text()").get().strip()
                        subCategorylink = subCategoryNode.xpath("./@href").get()
                        if not subCategorylink.startswith(store_url):
                            subCategorylink = store_url.rstrip('/') + subCategorylink
                        print("SUB CATEGORY  :", subCategoryTitle, "SUB CATEGORY LINK  :", subCategorylink)
                        category = topCategoryTitle + " " + categoryTitle + " " + subCategoryTitle
                        print("BreadCrum : ", category)
                        self.listing(subCategorylink, category)
                else:
                    subCategoryNodes = categoryLinkResponse.xpath(
                        "//div[contains(@class,'sidebar--categories')]/div/aside/h2/following-sibling::ul/li/a[not(contains(text(),'All'))]")
                    for subCategoryNode in subCategoryNodes:
                        subCategoryTitle = subCategoryNode.xpath("./text()").get().strip()
                        subCategorylink = subCategoryNode.xpath("./@href").get()
                        if not subCategorylink.startswith(store_url):
                            subCategorylink = store_url.rstrip('/') + subCategorylink
                        print("SUB CATEGORY  :", subCategoryTitle, "SUB CATEGORY LINK  :", subCategorylink)
                        category = topCategoryTitle + " " + categoryTitle + " " + subCategoryTitle
                        print("BreadCrum : ", category)
                        self.listing(subCategorylink, category)
        return Spider_BaseClass.AllProductUrls

    def listing(self, categorylink, category):
        categoryLinkResponse = requests.get(categorylink, stream=True)
        categoryLinkResponse = HtmlResponse(url=categorylink, body=categoryLinkResponse.text, encoding='utf-8')
        product_list = categoryLinkResponse.xpath(
            "//a[contains(@class,'product-link')]/@href").extract()
        for productUrl in product_list:
            if not productUrl.startswith(store_url):
                productUrl = store_url.rstrip('/') + productUrl
            if re.search('https://', productUrl) and re.search('\?', productUrl):
                productUrl = 'https://' + productUrl.split('https://')[1].split('?')[0].strip()
            print("Product URL  :", productUrl)
            Spider_BaseClass.AllProductUrls.append(productUrl)
            siteMapCategory = str(Spider_BaseClass.ProductUrlsAndCategory.get(productUrl)).replace('None', '')
            if siteMapCategory:
                Spider_BaseClass.ProductUrlsAndCategory[productUrl] = siteMapCategory + " " + category
            else:
                Spider_BaseClass.ProductUrlsAndCategory[productUrl] = category
        try:
            pageNo = ''
            nextPage = categoryLinkResponse.xpath(
                "//a[@rel='next' and contains(@href, 'javascript:setPageNumber') and not(contains(@href, 'javascript:void(0);'))]/@href").get()

            if re.search('\(', str(nextPage)):
                pageNo = str(nextPage).split('(')[1].split(')')[0]

            if pageNo:
                if re.search('pageNum=', categorylink):
                    categorylink = categorylink.split('pageNum')[0].rstrip('? | &')

                if re.search('\?', categorylink):
                    nextPageUrl = categorylink + '&pageNum=' + str(pageNo) + ''
                else:
                    nextPageUrl = categorylink + '?pageNum=' + str(pageNo) + ''

                print('nextPageUrl:', nextPageUrl)
                self.listing(nextPageUrl, category)
        except:
            print('pass')
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
        name = str(response.xpath("//h1[contains(@class,'product-name')]/text()").get()).strip()
        if not color == '' and not re.search(color, name, re.I):
            name = name + " - " + color
        return name

    def GetSelectedColor(self, response):
        return response.xpath(
            "//div[contains(@class,'product-sections') and contains(div/text(),'Color')]/span[contains(@class,'selectedColor')]/text()").get()

    def GetPrice(self, response):
        orignalPrice = response.xpath("//div[@id='fullPriceContainer']/span[contains(@id,'retailPrice')]/text()").get()
        if orignalPrice != None:
            return float(str(orignalPrice).replace('$', '').replace(',', ''))
        # else:
        #     regularPrice = response.xpath(
        #         "//div[contains(@class,'itemPriceWrap ')]/span[contains(@class,'priceWas')]/span/span[contains(@class,'USD')]/text()").get()
        #
        #     return float(str(regularPrice).replace('$', '').replace(',', ''))

    def GetSalePrice(self, response):
        salePrice = response.xpath(
            "//div[@id='salePriceContainer']/span[contains(@class,'price__sale')]/text()").get()
        if salePrice != None:
            return float(str(salePrice).replace("$", "").replace(',', ''))
        else:
            return 0

    def GetBrand(self, response):
        return str(response.xpath("//a[@property='brand']/span/following-sibling::text()").get()).strip()

    def GetImageUrl(self, response):
        imageUrls = []
        images = response.xpath("//div[@class='slideshow__pager']/a[img[not(@data-swatch)]]/@data-image").extract()
        for image in images:
            imageUrls.append(image)
        return imageUrls

    def GetDescription(self, response):
        return ' '.join(response.xpath("//div[@id='product-details__description']/ul/li/text()").extract()).replace(
            '\n', '').strip()

    def GetSizes(self, response):
        productSizes = []
        colorName = self.GetSelectedColor(response)
        sizeOptions = response.xpath(
            "//div[contains(@class,'product-sizes')]/ul/li/input[not(@disabled)]/following-sibling::label/span[contains(text(),'Size')]/following-sibling::span/text()").extract()
        for sizeName in sizeOptions:
            available = True

            if re.search(r'\bP(\d+|\w+)\b|\b(\d+|\w+)P\b', sizeName, re.IGNORECASE):
                fitType = "Petite"
            elif re.search(r'\b(\d+|\w+)X\b|\b(\d+|\w+)W\b', sizeName, re.IGNORECASE):
                fitType = "Plus"
            elif re.search(r'\bT(\d+|\w+)\b|\b(\d+|\w+)T\b', sizeName, re.IGNORECASE):
                fitType = "Tall"
            else:
                fitType = "Regular"
            sizelist = str(colorName), str(sizeName), available, str(fitType), 0.0, 0.0
            productSizes.append(sizelist)
        return productSizes

    def GetCategory(self, response):
        filterList = []
        if GetterSetter.ProductUrl in Spider_BaseClass.ProductUrlsAndCategory:
            categories = Spider_BaseClass.ProductUrlsAndCategory[GetterSetter.ProductUrl]
            for category in str(categories).split('$'):
                filterList.append(category)
        filters = '$'.join(map(str, filterList))
        return 'Women ' + filters
