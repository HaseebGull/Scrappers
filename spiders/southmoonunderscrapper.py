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


class Southmoonunderscrapper(shopify):
    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(Southmoonunderscrapper, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        return spider

    def GetProductUrls(self, homePageResponse):
        # ========== Category And Subcategory ==========#
        global topCategoryLink
        topCategoryNodes = homePageResponse.xpath(
            "//nav[contains(@class,'SidebarMenu__Nav--primary')]/div[contains(button/text(),'WOMEN') or contains(a/text(),'NEW') or contains(a/text(),'SALE')]")
        for topCategoryNode in topCategoryNodes:
            if not topCategoryNode.xpath("./button/text()"):
                topCategoryTitle = topCategoryNode.xpath("./a/text()").get().strip()
                topCategoryLink = topCategoryNode.xpath("./a/@href").get().strip()
                if not topCategoryLink.startswith(store_url):
                    topCategoryLink = store_url.rstrip('/') + topCategoryLink
            else:
                topCategoryTitle = topCategoryNode.xpath("./button/text()").get().strip()

            categoryNodes = topCategoryNode.xpath(
                "./div/div/div/a[contains(text(),'DRESSES') or contains(text(),'Dresses') or contains(text(),'Sets')]")
            if not categoryNodes:
                category = topCategoryTitle
                self.listing(topCategoryLink, category)
            for categoryNode in categoryNodes:
                categoryTitle = categoryNode.xpath("./text()").get().strip().replace('&amp;', '&')
                categorylink = categoryNode.xpath("./@href").get()
                if not categorylink.startswith(store_url):
                    categorylink = store_url.rstrip('/') + categorylink
                category = topCategoryTitle + " " + categoryTitle
                self.listing(categorylink, category)
        return Spider_BaseClass.AllProductUrls

    def listing(self, categorylink, category):
        categoryLinkResponse = requests.get(categorylink)
        categoryLinkResponse = HtmlResponse(url=categorylink, body=categoryLinkResponse.text, encoding='utf-8')
        product_list = categoryLinkResponse.xpath("//h2[contains(@class,'ProductItem__Title ')]/a/@href").extract()
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

    def GetProducts(self, response):
        ignorProduct = self.IgnoreProduct(response)
        if ignorProduct == True:
            self.ProductIsOutofStock(GetterSetter.ProductUrl)
        shopify.productJson = json.loads(self.SetProductJson(response))
        categoryAndName = shopify.GetCategory(self, response) + " " + self.GetName(response)
        if (re.search(r'\b' + 'NEW' + r'\b', categoryAndName, re.IGNORECASE) or
            re.search(r'\b' + 'SALE' + r'\b', categoryAndName, re.IGNORECASE)) and not \
                re.search(r'\b((shirt(dress?)|jump(suit?)|dress|gown|rompers|set|suit|caftan)(s|es)?)\b',
                          categoryAndName, re.IGNORECASE):
            print('Skipping Non Dress Product')
            self.ProductIsOutofStock(GetterSetter.ProductUrl)
        else:
            self.GetProductInfo(response)

    def GetName(self, response):
        color = self.GetSelectedColor(response)
        name = shopify.GetName(self, response)
        if not color == '' and not re.search(color, name):
            name = name + ' - ' + color
        return name

    def GetSelectedColor(self, response):
        return response.xpath(
            "//button[contains(span/text(),'Color')]/span/span/text()").get().strip()

    def IgnoreProduct(self, response):
        if re.search('"availability":', response.text):
            productAvailability = response.text.split('"availability":')[1].split(',')[0].strip()
            if not 'InStock' in productAvailability:
                return True
            else:
                return False
