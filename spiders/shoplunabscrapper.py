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

Spider_BaseClass.testingGender = 'Women'


class ShoplunabScrapper(shopify):
    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(ShoplunabScrapper, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        return spider

    def GetProductUrls(self, homePageResponse):
        # ========== Category And Subcategory ==========#
        topCategoryNodes = homePageResponse.xpath(
            """//div[@id='dl-menu']/ul/li[a[contains(text(),"What's New") or contains(text(),'CLOTHES') or contains(text(),'Sale')]]""")
        for topCategoryNode in topCategoryNodes:
            topCategoryNodeTitle = topCategoryNode.xpath("./a/text()").get().strip()
            topCategoryNodelink = topCategoryNode.xpath("./a/@href").get()
            if not topCategoryNodelink.startswith(store_url):
                topCategoryNodelink = store_url.rstrip('/') + topCategoryNodelink
            categoryNodes = topCategoryNode.xpath(
                "./ul/li/a[contains(text(),'Dresses') or contains(text(),'DRESSES') or contains(text(),'Rompers') or contains(text(),'ROMPERS') or contains(text(),'Sets') or contains(text(),'Bodysuits')]")
            if not categoryNodes:
                category = 'Women ' + topCategoryNodeTitle
                self.listing(topCategoryNodelink, category)
            else:
                for categoryNode in categoryNodes:
                    categoryNodeTitle = categoryNode.xpath("./text()").get().strip()
                    categoryNodelink = categoryNode.xpath("./@href").get()
                    if not categoryNodelink.startswith(store_url):
                        categoryNodelink = store_url.rstrip('/') + categoryNodelink
                    category = 'Women ' + topCategoryNodeTitle + " " + categoryNodeTitle
                    self.listing(categoryNodelink, category)
        return Spider_BaseClass.AllProductUrls

    def listing(self, categorylink, category):
        categoryLinkResponse = requests.get(categorylink)
        categoryLinkResponse = HtmlResponse(url=categorylink, body=categoryLinkResponse.text, encoding='utf-8')
        product_list = categoryLinkResponse.xpath(
            "//div[@class='product-info-inner']/a/@href").extract()
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
            nextPageUrl = categoryLinkResponse.xpath("//div[@class='paginext']/a/@href").extract()[0]
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
            re.search('sets', categoryAndName, re.IGNORECASE) or
            re.search("What's New", categoryAndName, re.IGNORECASE)) and not \
                re.search(r'\b((shirt(dress?)|jump(suit?)|dress|set|gown|suit|caftan)(s|es)?)\b', categoryAndName,
                          re.IGNORECASE):
            print('Skipping Non Dress Product')
            self.ProductIsOutofStock(GetterSetter.ProductUrl)
        else:
            self.GetProductInfo(response)

    def GetName(self, response):
        color = self.GetSelectedColor(response)
        name = shopify.GetName(self, response)
        if not color == '' and not re.search(color, name):
            name = name + '-' + color
        return name

    def GetSelectedColor(self, response):
        try:
            return response.xpath(
                "//div[@class='swatch clearfix'][div[@class='header' and contains(text(),'Color')]]/div/div/text()").get().strip()
        except:
            return ''

    def IgnoreProduct(self, response):
        if re.search('"availability":', response.text):
            productAvailability = response.text.split('"availability":')[1].split(',')[0].strip()
            if not 'InStock' in productAvailability:
                return True
            else:
                return False
