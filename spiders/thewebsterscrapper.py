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


class TheWebsterScrapper(magento):
    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(TheWebsterScrapper, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        return spider

    def GetProductUrls(self, homePageResponse):
        # ========== Category And Subcategory ==========#
        topCategoryNodes = homePageResponse.xpath(
            "//nav[@class='navigation']/ul/li[a[contains(span/text(),'Women') or contains(span/text(),'Men') or "
            "contains(span/text(),'Sale')]]")
        for topCategoryNode in topCategoryNodes:
            topCategoryTitle = topCategoryNode.xpath("./a/span/text()").get().strip()
            topCategorylink = topCategoryNode.xpath("./a/@href").get()
            if not topCategorylink.startswith(store_url):
                topCategorylink = store_url.rstrip('/') + topCategorylink
            categoryNodes = topCategoryNode.xpath(
                "./div[@id='navigation-cms-" + str(topCategoryTitle).lower() + "']/div/div/div/div[contains("
                                                                               "div/p/strong/span/a/text(),"
                                                                               "'CLOTHING') or "
                                                                               " contains(div/p/span/a/strong/text(),"
                                                                               "'WOMEN') or contains("
                                                                               "div/p/span/a/strong/text(),'MEN')]")
            for categoryNode in categoryNodes:
                try:
                    categoryTitle = categoryNode.xpath("./div/p/span/a/strong/text()").get().strip()
                except:
                    categoryTitle = categoryNode.xpath("./div/p/strong/span/a/text()").get().strip()
                subCategoryNodes = categoryNode.xpath(
                    "./div/ul/li/a[contains(text(),'Dress') or contains(text(),'Suits') or contains(text(),'Clothing') and not(contains(text(),'All'))]")
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
        product_list = categoryPageResponse.xpath("//a[contains(@class,'product-item-photo')]/@href").extract()
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
            nextpageUrl = \
                categoryPageResponse.xpath("//link[@rel='next']/@href").extract()[0]
            if not nextpageUrl.startswith(store_url):
                nextpageUrl = store_url.rstrip('/') + nextpageUrl
            self.listing(nextpageUrl, category)
        except:
            pass

    def GetProducts(self, response):
        ignorProduct = self.IgnoreProduct(response)
        if ignorProduct == True:
            self.ProductIsOutofStock(GetterSetter.ProductUrl)
        else:
            categoryAndName = self.GetCategory(response) + " " + self.GetName(response)
            if (re.search('Sale', categoryAndName, re.IGNORECASE)) and not \
                    re.search(r'\b((shirt(dress?)|jump(suit?)|dress|set|romper|gown|suit|caftan)(s|es)?)\b',
                              categoryAndName,
                              re.IGNORECASE):
                print('Skipping Non Dress Product')
                self.ProductIsOutofStock(GetterSetter.ProductUrl)
            else:
                jsonStr = self.SetProductJson(response.text)
                if jsonStr != '':
                    magento.productJson = json.loads(jsonStr)
                global productID
                productID = response.xpath("//div[contains(@class,'price-box')]/@data-product-id").get()
                self.GetProductInfo(response)

    def SetProductJson(self, response):
        if re.search('"jsonConfig": ', response):
            return str(response.split('"jsonConfig": ')[1].split('"jsonSwatchConfig"')[0]).strip().rstrip(',')
        return ''

    def GetName(self, response):
        color = self.GetSelectedColor(response)
        name = response.xpath("//h1[@class='page-title']/span[@class='base']/text()").get().strip()
        if not color == '' and not re.search(color, name):
            name = name + ' - ' + color
        return name

    def GetSelectedColor(self, response):
        try:
            colorJson = json.loads(response.xpath(
                """//script[@type='application/ld+json' and contains(text(),'"@type": "Product"')]/text()""").get())
            color = str(colorJson['sku']).split('-')[1]
        except:
            color = ''
        return color

    def GetPrice(self, response):
        orignalPrice = magento.productJson['prices']['oldPrice']['amount']
        if orignalPrice != None:
            return float(str(orignalPrice).replace('$', '').replace(',', ''))

    def GetSalePrice(self, response):
        salePrice = magento.productJson['prices']['finalPrice']['amount']
        if salePrice:
            return float(str(salePrice).replace('$', '').replace(',', ''))
        else:
            return 0

    def GetDescription(self, response):
        description = ','.join(response.xpath("//div[contains(@class,'description')]/div/ul/li/text()").extract())
        if description is '':
            description = ','.join(response.xpath("//div[contains(@class,'description')]/div/p/text()").extract())
        return description

    def GetBrand(self, response):
        return response.xpath("//h1[@class='page-title']/span[contains(@class,'manufacturer')]/a/text()").get().strip()

    def GetSizes(self, response):
        sizeList = []
        color = ''
        sizes = magento.GetSizes(self, response)
        color = self.GetSelectedColor(response)
        for size in sizes:
            sizeList.append([color, size[1], size[2], size[3], size[4], size[5]])
        return sizeList

    def GetCategory(self, response):
        siteMapCategory = str(Spider_BaseClass.ProductUrlsAndCategory.get(GetterSetter.ProductUrl)).replace('None', '')
        return siteMapCategory.strip()
