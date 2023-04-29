import re
import sys
from pathlib import Path

DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(DIR.parent.parent.parent.parent))
__package__ = DIR.name

import django

django.setup()
from scrapy import signals

from Magento import *

store_url = sys.argv[4]


class MensSuitHabitScrapper(magento):
    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(MensSuitHabitScrapper, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        return spider

    def GetProductUrls(self, homePageResponse):
        # ========== Category And Subcategory ==========#
        topCategoryNodes = homePageResponse.xpath(
            "//nav[contains(@class,'navigation')]/ul/li[a[contains(span/text(),'Suits') or contains(span/text(),'Tuxedos') or contains(span/text(),'Shirts') or contains(span/text(),'Pants')]]")
        for topCategoryNode in topCategoryNodes:
            topCategoryTitle = topCategoryNode.xpath("./a/span/text()").get().strip()
            topCategorylink = topCategoryNode.xpath("./a/@href").get()
            if not topCategorylink.startswith(store_url):
                topCategorylink = store_url.rstrip('/') + topCategorylink
            categoryNodes = topCategoryNode.xpath(
                "./div//ul/li/a[not(contains(span/text(),'All')) and not(contains(span/text(),'Casual')) and not(contains(span/text(),'Jeans')) and not(contains(span/text(),'Sport Coats'))]")
            if not categoryNodes:
                category = topCategoryTitle
                self.listing(topCategorylink, category)
            else:
                for categoryNode in categoryNodes:
                    categoryTitle = categoryNode.xpath("./span/text()").get().strip()
                    categorylink = categoryNode.xpath("./@href").get()
                    if not categorylink.startswith(store_url):
                        categorylink = store_url.rstrip('/') + categorylink
                    category = topCategoryTitle + " " + categoryTitle
                    if not "Men’s" in category:
                        category = 'Men’s' + " " + topCategoryTitle + " " + categoryTitle
                    self.listing(categorylink, category)
        return Spider_BaseClass.AllProductUrls

    def listing(self, categorylink, category):
        categoryLinkResponse = requests.get(categorylink, stream=True)
        categoryLinkResponse = HtmlResponse(url=categorylink, body=categoryLinkResponse.text, encoding='utf-8')
        product_list = categoryLinkResponse.xpath(
            "//a[@class='product-item-link']/@href").extract()
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
            nextPageUrl = categoryLinkResponse.xpath(
                "//li[@class='item pages-item-next']/a[@class='action  next']/@href").get()
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
            jsonStr = self.SetProductJson(response.text)
            if jsonStr != '':
                magento.productJson = json.loads(jsonStr)
            global productID
            productID = response.xpath("//input[@name='product']/@value").get()
            self.GetProductInfo(response)

    def SetProductJson(self, response):
        if re.search('"spConfig": ', response):
            return str(response.split('"spConfig": ')[1].split('"gallerySwitchStrategy":')[0]).strip().rstrip(',')
        return ''

    def GetName(self, response):
        name = response.xpath("//span[@itemprop='name']/text()").get().strip()
        color = self.GetSelectedColor(response)
        if not color == '' and not re.search(color, name, re.I):
            name = name + " - " + color
        return name

    def GetSelectedColor(self, response):
        try:
            sku = str(response.xpath("//div[@itemprop='sku']/text()").get().strip()).split('-')[-1]
            color = re.search(r'\b(' + sku + r')\b'r'|\b(' + sku + r')\w+',
                              response.xpath("//span[@itemprop='name']/text()").get().strip(),
                              re.IGNORECASE).group(0)
            return color
        except:

            return ''

    def GetPrice(self, response):
        orignalPrice = response.xpath(
            "//div[@data-product-id='" + str(
                productID) + "']/span[contains(@class,'old-price')]/span/span[@data-price-type='oldPrice']/span/text()").get()
        if orignalPrice != None:
            return float(str(orignalPrice).replace('$', '').replace(',', ''))
        else:
            regularPrice = response.xpath(
                "//div[@data-product-id='" + str(
                    productID) + "']/span[contains(@class,'old-price')]/span/span[@data-price-type='oldPrice']/span/text()").get()
            return float(str(regularPrice).replace('$', '').replace(',', ''))

    def GetSalePrice(self, response):
        salePrice = response.xpath(
            "//div[@data-product-id='" + str(
                productID) + "']/span[contains(@class,'special-price')]/span/span[@data-price-type='finalPrice']/span/text()").get()
        if salePrice:
            return float(str(salePrice).replace('$', '').replace(',', ''))
        else:
            return 0

    def IgnoreProduct(self, response):
        productAvailability = response.xpath("//div[@title='Availability']/span[2]/text()").get().strip()
        if not 'In stock' in productAvailability:
            return True
        else:
            return False

    def GetDescription(self, response):
        return ','.join(response.xpath("//div[@itemprop='description']/ul/li/text()").extract())

    def GetBrand(self, response):
        return 'Mens Suit Habit'

    def GetSizes(self, response):
        sizeList = []
        color = self.GetSelectedColor(response)
        sizes = magento.GetSizes(self, response)
        for size in sizes:
            sizeList.append([color, size[1].strip(), size[2], size[3], size[4], size[5]])
        return sizeList
