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


class Dylanlexscrapper(shopify):
    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(Dylanlexscrapper, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        return spider

    def GetProductUrls(self, homePageResponse):
        # ========== Category And Subcategory ==========#
        topCategoryNodes = homePageResponse.xpath(
            "//div[contains(@class,'top-nav')]/div/ul/li[a[contains(text(),'Clothing') or contains(text(),'SET')]]")
        for topCategoryNode in topCategoryNodes:
            topCategoryTitle = topCategoryNode.xpath("./a/text()").get().strip()
            topCategorylink = topCategoryNode.xpath("./a/@href").get().strip()
            if not topCategorylink.startswith(store_url):
                topCategorylink = store_url.rstrip('/') + topCategorylink
            categoryNodes = topCategoryNode.xpath("./ul/li/a[contains(text(),'Dresses')]")
            if not categoryNodes:
                category = "Women " + topCategoryTitle
                self.listing(topCategorylink, category)
            else:
                for categoryNode in categoryNodes:
                    categoryTitle = categoryNode.xpath("./text()").get().strip()
                    categorylink = categoryNode.xpath("./@href").get()
                    if not categorylink.startswith(store_url):
                        categorylink = store_url.rstrip('/') + categorylink
                    category = "Women " + topCategoryTitle + " " + categoryTitle
                    self.listing(categorylink, category)
        return Spider_BaseClass.AllProductUrls

    def listing(self, categorylink, category):
        categoryLinkResponse = requests.get(categorylink)
        categoryLinkResponse = HtmlResponse(url=categorylink, body=categoryLinkResponse.text, encoding='utf-8')
        product_list = categoryLinkResponse.xpath("//div[contains(@class,'image-section')]/a/@href").extract()
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
            nextPageUrl = categoryLinkResponse.xpath("//link[@rel='next']/@href").extract()[0]
            if not nextPageUrl.startswith(store_url):
                nextPageUrl = store_url.rstrip('/') + nextPageUrl
            self.listing(nextPageUrl, category)
        except:
            pass

    def SetproductJson(self, response):
        if re.search('SwymProductInfo.product = {', response.text):
            ProductJsonStr = '{' + response.text.split('SwymProductInfo.product = {')[1].split('"content"')[
                0].strip().rstrip(',') + '}'
        elif re.search('afterpay_product = {', response.text):
            ProductJsonStr = '{' + response.text.split('afterpay_product = {')[1].split('"content"')[0].strip().rstrip(
                ',') + '}'
        else:
            print("Invoke product json api for: ", GetterSetter.ProductUrl)
            ProductJsonStr = requests.get(GetterSetter.ProductUrl + '.js', cookies=Spider_BaseClass.cookiesDict).content

        return ProductJsonStr

    def GetName(self, response):
        color = self.GetSelectedColor(response)
        name = shopify.GetName(self, response)
        if not color == '' and not re.search(color, name):
            name = name + ' - ' + color
        return name

    def GetSelectedColor(self, response):
        try:
            selectedColor = response.xpath(
                "//div[@class='color_swatches']/p/following-sibling::div/label[1]/input/@value").get().strip()
            return selectedColor
        except:
            return ''

    def IgnoreProduct(self, response):
        if re.search('"availability":', response.text):
            productAvailability = response.text.split('"availability":')[1].split(',')[0].strip()
            if not 'InStock' in productAvailability:
                return True
            else:
                return False
