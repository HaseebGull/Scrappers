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

class CottononScrapper(Spider_BaseClass):
    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(CottononScrapper, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        return spider

    def GetProductUrls(self, homePageResponse):
        # ========== Category And Subcategory ==========#
        brandsNodes = homePageResponse.xpath(
            "(//ul[contains(@class,'wiper-wrapper')])[1]/li/a[contains(@title,'Cotton On') or contains(@title,'Kids')]")
        for brandsNode in brandsNodes:
            brandLink = brandsNode.xpath("./@href").get()
            if not brandLink.startswith(store_url):
                brandLink = store_url.rstrip('/') + brandLink

            brandLinkResponse = requests.get(brandLink)
            brandLinkResponse = HtmlResponse(url=brandLink, body=brandLinkResponse.text, encoding='utf-8')
            topCategoryNodes = brandLinkResponse.xpath(
                "//nav[@id='mega-menu']/ul/li[a[contains(text(),'Women') or contains(text(),'Men') or contains(text(),'Girls') or contains(text(),'Boy') or contains(text(),'Baby') or contains(text(),'Sale') ]]")
            for topCategoryNode in topCategoryNodes:
                topCategoryTitle = topCategoryNode.xpath("./a/text()").get().strip()
                categoryNodes = topCategoryNode.xpath(
                    "./ul/div/div/div/ul/li[a[contains(text(),'Clothing') or contains(text(),'Womens Sale') or contains(text(),'Sale Dresses')]]")
                for categoryNode in categoryNodes:
                    categoryTitle = categoryNode.xpath("./a/text()").get().strip()
                    categorylink = categoryNode.xpath("./a/@href").get()
                    if not categorylink.startswith(store_url):
                        categorylink = store_url.rstrip('/') + categorylink
                    if topCategoryTitle == 'Sale' and categoryTitle == 'Sale Dresses and Skirts':
                        category = "Baby " + topCategoryTitle + " " + categoryTitle
                        self.listing(categorylink, category)
                    subCategoryNodes = categoryNode.xpath(
                        "./span/a[contains(text(),'Dress') or contains(text(),'Pents') or contains(text(),'Suits') or contains(text(),'Bodysuits')]")
                    for subCategoryNode in subCategoryNodes:
                        subCategoryTitle = subCategoryNode.xpath("./text()").get().strip()
                        subCategorylink = subCategoryNode.xpath("./@href").get()
                        if not subCategorylink.startswith(store_url):
                            subCategorylink = store_url.rstrip('/') + subCategorylink
                        category = topCategoryTitle + " " + categoryTitle + " " + subCategoryTitle
                        self.listing(subCategorylink, category)
        return Spider_BaseClass.AllProductUrls

    def listing(self, categorylink, category):
        CategoryLinkResponse = requests.get(categorylink)
        categoryPageResponse = HtmlResponse(url=categorylink, body=CategoryLinkResponse.text, encoding='utf-8')
        product_list = categoryPageResponse.xpath("//a[contains(@class,'name-link')]/@href").extract()
        for productUrl in product_list:
            if not productUrl.startswith(store_url):
                productUrl = store_url.rstrip('/') + productUrl
            if re.search('https://', productUrl) and re.search('&', productUrl):
                productUrl = 'https://' + productUrl.split('https://')[1].split('&')[0].strip()
            Spider_BaseClass.AllProductUrls.append(productUrl)
            siteMapCategory = str(Spider_BaseClass.ProductUrlsAndCategory.get(productUrl)).replace('None', '')
            if siteMapCategory:
                Spider_BaseClass.ProductUrlsAndCategory[productUrl] = siteMapCategory + " " + category
            else:
                Spider_BaseClass.ProductUrlsAndCategory[productUrl] = category
        try:
            nextpageUrl = \
                categoryPageResponse.xpath("//link[@rel='next']/@href").get()
            if not nextpageUrl.startswith(store_url):
                nextpageUrl = store_url.rstrip('/') + nextpageUrl
            self.listing(nextpageUrl, category)
        except:
            pass

    def GetProducts(self, response):
        ignorProduct = self.IgnoreProduct(response)
        if ignorProduct == True:
            self.ProductIsOutofStock(GetterSetter.ProductUrl)
        categoryAndName = self.GetCategory(response) + " " + self.GetName(response)
        if (re.search('Skirts', categoryAndName, re.IGNORECASE)) and not \
                re.search(r'\b((shirt(dress?)|jump(suit?)|dress|gown|suit|caftan)(s|es)?)\b', categoryAndName,
                          re.IGNORECASE):
            print('Skipping Non Dress Product')
            self.ProductIsOutofStock(GetterSetter.ProductUrl)
        else:
            self.GetProductInfo(response)

    def GetName(self, response):
        color = self.GetSelectedColor(response)
        name = response.xpath("//h1[contains(@class,'product-name')]/text()").get().strip()
        if not color == '' and not re.search(color, name):
            name = name + ' - ' + color
        return name

    def GetSelectedColor(self, response):
        try:
            return str(
                response.xpath("//div[@class='value color']//li[contains(@class,'selectable selected')]/a/@title").get().strip()).replace(
                'Select Color:', '').title().strip()
        except Exception as e:
            print(e)
            return ''

    def GetPrice(self, response):
        orignalPrice = response.xpath(
            "//div[@class='product-price']/span[contains(@class,'price-standard')]/text()").get()
        if orignalPrice != None:
            return float(str(orignalPrice).replace('$', '').replace(',', ''))
        else:
            regularPrice = response.xpath(
                "//div[@class='product-price']/span[@class='price-sales']/text()").get()
            return float(str(regularPrice).replace('$', '').replace(',', ''))

    def GetSalePrice(self, response):
        salePrice = response.xpath(
            "//div[@class='product-price']/span[@class='price-sales']/text()").get()
        if salePrice:
            return float(str(salePrice).replace('$', '').replace(',', ''))
        else:
            return 0

    def GetDescription(self, response):
        try:
            feature = ','.join(response.xpath("//div[@id='features-tab']/ul/li/text()").extract())
        except:
            feature = ''
        try:
            description = response.xpath("//div[@id='description-tab']/div/div/pre/text()").get()
        except:
            description = ''
        try:
            care = response.xpath("//div[@id='care-tab']/div/div/pre/text()").get()
        except:
            care = ''
        try:
            composition = response.xpath(
                "//div[@id='features-tab']/div/div[contains(text(),'Composition')]/following-sibling::div/text()").get()
        except:
            composition = ''

        description = str(feature).replace('None', '') + " " + str(composition).replace('None', '') + " " + str(
            description).replace('None', '') + " " + str(care).replace('None', '')
        return description

    def GetBrand(self, response):
        brand = ''
        if re.search('"brand":"', response.text):
            brand = response.text.split('"brand":"')[1].split('",')[0].strip()
        return brand

    def GetImageUrl(self, response):
        imageUrls = []
        images = response.xpath("//li[contains(@class,'thumb')]/a/img/@src").extract()
        for image in images:
            imageUrls.append(str(image).replace('sw=104&sh=156&sm=fit', 'sw=640&sh=960&sm=fit'))
        return imageUrls

    def GetSizes(self, response):
        sizes = []
        sizeList = response.xpath(
            "//ul[contains(@class,'swatches online size')] /li[contains(@class,'selectable')]/a/span/text()").extract()
        gender = ProductFilters.objects.get(ProductUrl=GetterSetter.ProductUrl).ParentCategory.split(',')[0]
        color = self.GetSelectedColor(response)
        for size in sizeList:
            available = True
            fitType = GetFitType(gender, size)
            sizes.append([color, size, available, fitType, 0.0, 0.0])
        return sizes

    # def IgnoreProduct(self, response):
    #     if re.search('"availability":', response.text):
    #         productAvailability = response.text.split('"availability":')[1].split(',')[0].strip()
    #         if not 'InStock' in productAvailability:
    #             return True
    #         else:
    #             return False

    def GetCategory(self, response):
        siteMapCategory = str(Spider_BaseClass.ProductUrlsAndCategory.get(GetterSetter.ProductUrl)).replace('None', '')
        return siteMapCategory.strip()
