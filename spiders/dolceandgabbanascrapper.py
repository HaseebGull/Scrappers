import sys
from pathlib import Path

DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(DIR.parent.parent.parent.parent))
__package__ = DIR.name

import django

django.setup()
from BaseClass import *
from scrapy import signals
import lxml.html

store_url = sys.argv[4]


class DolceandGabbanaScrapper(Spider_BaseClass):
    # Spider_BaseClass.testingGender = 'Women '
    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(DolceandGabbanaScrapper, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        return spider

    def GetProductUrls(self, homePageResponse):
        # url1 = 'https://us.dolcegabbana.com/en/men/clothing/shirts/silk-jacquard-mazzini-fit-shirt-multicolor-G5GZ3TFJ1HOS8350.html?cgid=men-apparel-shirts'
        # Spider_BaseClass.AllProductUrls.append(url1)
        # Spider_BaseClass.ProductUrlsAndCategory[url1] = "Men Shirt"
        # ========== Category And Subcategory ==========#
        topCategoryNodes = homePageResponse.xpath(
            "//ul[contains(@class,'menu_category-ul')]/li[a[contains(text(),'Women') or contains(text(),'Men') or contains(text(),'Children')]]")
        for topCategoryNode in topCategoryNodes:
            topCategoryTitle = topCategoryNode.xpath("./a/text()").get().strip()
            topCategorylink = topCategoryNode.xpath("./a/@href").get()
            if not topCategorylink.startswith(store_url):
                topCategorylink = store_url.rstrip('/') + topCategorylink
            categoryNodes = topCategoryNode.xpath(
                "./nav/div/ul/li/div[a[contains(text(),'CLOTHING') or contains(text(),'BOY') or contains(text(),'GIRL')]]")
            for categoryNode in categoryNodes:
                categoryTitle = categoryNode.xpath("./a/text()").get().strip()
                categorylink = categoryNode.xpath("./a/@href").get()
                if not categorylink.startswith(store_url):
                    categorylink = store_url.rstrip('/') + categorylink
                subCategoryNodes = categoryNode.xpath(
                    "./div/ul/li/a[not(contains(div/text(),'T-Shirts')) and contains(div/text(),'Shirts') or contains(div/text(),'Dress') or contains(div/text(),'Suits') or contains(div/text(),'Babygrows')]")
                for subCategoryNode in subCategoryNodes:
                    subCategoryTitle = subCategoryNode.xpath("./div/text()").get().strip()
                    subCategorylink = subCategoryNode.xpath("./@href").get()
                    if not subCategorylink.startswith(store_url):
                        subCategorylink = store_url.rstrip('/') + subCategorylink
                    if topCategoryTitle == 'Women' and subCategoryTitle == 'Shirts and Tops' or \
                            'GIRL' in categoryTitle and subCategoryTitle == 'Shirts and Tops' or \
                            'BOY' in categoryTitle and subCategoryTitle == 'Shirts':
                        continue
                    category = topCategoryTitle + " " + categoryTitle + " " + subCategoryTitle
                    self.listing(subCategorylink, category)
        return Spider_BaseClass.AllProductUrls

    def listing(self, categorylink, category):
        categoryLinkResponse = requests.get(categorylink, stream=True)
        categoryLinkResponse = HtmlResponse(url=categorylink, body=categoryLinkResponse.text, encoding='utf-8')
        product_list = categoryLinkResponse.xpath(
            "//div[contains(@class,'b-product_image-container')]/div/div[1]/a/@href").extract()
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
            nextPageUrl = \
                categoryLinkResponse.xpath("//link[@rel='next']/@href").get()
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
            productJsonStr = response.xpath(
                """//script[@type='application/ld+json' and contains(text(),'"@type":"Product"')]/text()""").get()
            productjson = json.loads(productJsonStr)

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
        name = productjson['name']
        if not color == '' and not re.search(color, name, re.I):
            name = name + " - " + color
        return name

    def GetSelectedColor(self, response):
        selectedColor = productjson['color']
        return selectedColor

    def GetPrice(self, response):
        orignalPrice = productjson['offers']['price']
        if orignalPrice != None:
            return float(str(orignalPrice).replace('$', '').replace(',', ''))

    def GetSalePrice(self, response):
        salePrice = productjson['offers']['price']
        if salePrice != None:
            return float(str(salePrice).replace("$", "").replace(',', ''))
        else:
            return 0

    def GetBrand(self, response):
        return productjson['brand']['name']

    def GetImageUrl(self, response):
        imageUrls = []
        for image in productjson['image']:
            imageUrls.append(image)
        return imageUrls

    def GetDescription(self, response):
        return productjson['description']

    def GetSizes(self, response):
        productSizes = []
        colorName = self.GetSelectedColor(response)
        sizesHTML = response.xpath(
            "//script[@id='sizeFlyoutTemplate']/text()").get()

        sizesNodes = lxml.html.fromstring(sizesHTML)
        sizes = sizesNodes.xpath(
            "(//ul[contains(@class,'b-swatches_size')])[1]/li[not(contains(@class,'unselectable'))]/a/span/@data-attr-value")
        gender = ProductFilters.objects.get(ProductUrl=GetterSetter.ProductUrl).ParentCategory.split(',')[0]
        for size in sizes:
            sizeName = str(size).strip()
            available = True
            fitType = GetFitType(gender, sizeName)
            sizelist = str(colorName), str(sizeName), available, str(fitType), 0.0, 0.0
            productSizes.append(sizelist)
        return productSizes

    def GetCategory(self, response):
        siteMapCategory = str(Spider_BaseClass.ProductUrlsAndCategory[GetterSetter.ProductUrl]).replace('None', '')
        return siteMapCategory.strip()
