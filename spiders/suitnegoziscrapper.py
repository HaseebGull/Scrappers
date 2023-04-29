import sys
from pathlib import Path

DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(DIR.parent.parent.parent.parent))
__package__ = DIR.name

import django

django.setup()
from Shopify import *
from scrapy import signals

store_url = sys.argv[4]


class Suitnegoziscrapper(shopify):
    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(Suitnegoziscrapper, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        return spider

    def GetProductUrls(self, homePageResponse):
        # ========== Category And Subcategory ==========#
        topCategoryNodes = homePageResponse.xpath(
            "//ul[(@class='menu')]/li[a[contains(text(),'Woman') or contains(text(),'Man') or contains(text(),'NEW')]]")
        for topCategoryNode in topCategoryNodes:
            topCategoryTitle = topCategoryNode.xpath("./a/text()").get().strip()
            topCategorylink = topCategoryNode.xpath("./a/@href").get()
            if not topCategorylink.startswith(store_url):
                topCategorylink = store_url.rstrip('/') + topCategorylink
            categoryNodes = topCategoryNode.xpath(
                "./div/div/div/ul/li[a[contains(text(),'Clothing') or contains(text(),'Woman')]]")
            for categoryNode in categoryNodes:
                categoryTitle = categoryNode.xpath("./a/text()").get().strip()
                categorylink = categoryNode.xpath("./a/@href").get()
                if not categorylink.startswith(store_url):
                    categorylink = store_url.rstrip('/') + categorylink
                subCategoryNodes = categoryNode.xpath(
                    "./ul/li/a[contains(text(),'Dress') or contains(text(),'Suit')]")
                if not subCategoryNodes:
                    category = topCategoryTitle + " " + categoryTitle
                    self.listing(categorylink, category)
                else:
                    for subCategoryNode in subCategoryNodes:
                        subCategoryTitle = subCategoryNode.xpath("./text()").get().strip()
                        subCategorylink = subCategoryNode.xpath("./@href").get()
                        if not subCategorylink.startswith(store_url):
                            subCategorylink = store_url.rstrip('/') + subCategorylink
                        category = topCategoryTitle + " " + categoryTitle + " " + subCategoryTitle
                        self.listing(subCategorylink, category)
        return Spider_BaseClass.AllProductUrls

    def listing(self, categorylink, category):
        categoryLinkResponse = requests.get(categorylink)
        categoryLinkResponse = HtmlResponse(url=categorylink, body=categoryLinkResponse.text, encoding='utf-8')
        product_list = categoryLinkResponse.xpath("//div[contains(@class,'product-card__left')]/a/@href").extract()
        for productUrl in product_list:
            if not productUrl.startswith(store_url):
                productUrl = store_url.rstrip('/') + productUrl
            productUrl = self.GetCanonicalUrl(productUrl)
            Spider_BaseClass.AllProductUrls.append(productUrl)
            siteMapCategory = str(Spider_BaseClass.ProductUrlsAndCategory.get(productUrl)).replace('None', '')
            if siteMapCategory:
                Spider_BaseClass.ProductUrlsAndCategory[productUrl] = siteMapCategory + " " + category
            else:
                Spider_BaseClass.ProductUrlsAndCategory[productUrl] = category
        try:
            nextPageUrl = categoryLinkResponse.xpath("//div[@class='next']/a/@href").extract()[0]
            if not nextPageUrl.startswith(store_url):
                nextPageUrl = store_url.rstrip('/') + nextPageUrl
            self.listing(nextPageUrl, category)
        except:
            pass

    def GetProducts(self, response):
        ignorProduct = self.IgnoreProduct(response)
        if ignorProduct == True:
            self.ProductIsOutofStock(GetterSetter.ProductUrl)
        shopify.productJson = json.loads(self.SetProductJson(response))
        categoryAndName = shopify.GetCategory(self, response) + " " + self.GetName(response)
        if (re.search('sale', categoryAndName, re.IGNORECASE) or
            re.search(r'\b' + 'new in' + r'\b', categoryAndName, re.IGNORECASE)) and not re.search(
            r'\b((shirt(dress?)|jump(suit?)|dress|set|romper|gown|suit|caftan)(s|es)?)\b',
            categoryAndName, re.IGNORECASE):
            print('Skipping Non Dress Product')
            self.ProductIsOutofStock(GetterSetter.ProductUrl)
        else:
            self.GetProductInfo(response)

    def SetproductJson(self, response):
        if re.search('product: {', response.text):
            ProductJsonStr = '{' + response.text.split('product: {')[1].split('"content"')[
                0].strip().rstrip(
                ',') + '}'
        else:
            print("Invoke product json api for: ", GetterSetter.ProductUrl)
            ProductJsonStr = requests.get(GetterSetter.ProductUrl + '.js',
                                          cookies=Spider_BaseClass.cookiesDict).content
        return ProductJsonStr

    def GetSizes(self, response):
        sizeScale = ''
        color = self.GetSelectedColor(response)
        tags = shopify.productJson['tags']
        for scale in tags:
            if not 'sizerange' in scale:
                continue
            else:
                sizeScale = str(scale).replace('sizerange-type_', '')

        sizes = shopify.GetSizes(self, response)
        sizeList = []
        for size in sizes:
            mappedSize = sizeScale + " " + size[1]
            MappedSize = color, mappedSize, size[2], size[3], size[4], size[5]
            sizeList.append(MappedSize)
        return sizeList

    def GetName(self, response):
        color = self.GetSelectedColor(response)
        name = shopify.GetName(self, response)
        if not color == '' and not re.search(color, name):
            name = name + ' - ' + color
        return name

    def GetSelectedColor(self, response):
        colorStr = str(response.xpath(
            "//ul[contains(@class,'product-page__additional-info')]/li[contains(text(),'Color')]/text()").get().strip()).replace(
            'Color code: ', '')
        if re.search(r'[0-9]', colorStr):
            color = re.sub(r'[0-9]', '', colorStr)
            return color
        return colorStr

    def IgnoreProduct(self, response):
        productAvailability = response.xpath("//link[@itemprop='availability']/@href").get().strip()
        if not 'InStock' in productAvailability:
            return True
        else:
            return False
