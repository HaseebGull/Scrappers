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


class RebeccaMinkoffScrapper(shopify):
    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(RebeccaMinkoffScrapper, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        return spider

    def GetProductUrls(self, homePageResponse):
        # ========== Category And Subcategory ==========#
        topCategoryNodes = homePageResponse.xpath(
            "//nav[@class='NavigationMenuDesktop__nav']/ul/li/a[contains(text(),'Clothing')]")
        for topCategoryNode in topCategoryNodes:
            topCategoryNodeTitle = topCategoryNode.xpath("./text()").get().strip()
            topCategoryNodelink = topCategoryNode.xpath("./@href").get()
            sublink = topCategoryNodelink
            if not topCategoryNodelink.startswith(store_url):
                topCategoryNodelink = store_url.rstrip('/') + topCategoryNodelink
            subCategoryNodes = homePageResponse.xpath(
                "//div[contains(@data-sublinks,'" + sublink + "')]/div/div/ul/li[a/span[text()='Dresses & Skirts' or text()='New Arrivals' or text()='Sale']]")
            for subCategoryNode in subCategoryNodes:
                subCategoryNodeTitle = subCategoryNode.xpath("./a/span/text()").get().strip()
                subCategoryNodelink = subCategoryNode.xpath("./a/@href").get()
                if not subCategoryNodelink.startswith(store_url):
                    subCategoryNodelink = store_url.rstrip('/') + subCategoryNodelink
                category = 'Women ' + topCategoryNodeTitle + " " + subCategoryNodeTitle
                self.listing(subCategoryNodelink, category)
        return Spider_BaseClass.AllProductUrls

    def listing(self, categorylink, category):
        categoryLinkResponse = requests.get(categorylink)
        categoryLinkResponse = HtmlResponse(url=categorylink, body=categoryLinkResponse.text, encoding='utf-8')
        product_list = categoryLinkResponse.xpath(
            "//a[@class='ProductCard__info']/@href").extract()
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

    def IgnoreProduct(self, response):
        if re.search('"availability":', response.text):
            productAvailability = response.text.split('"availability":')[1].split(',')[0].strip()
            if not 'InStock' in productAvailability:
                return True
            else:
                return False

    def GetProducts(self, response):
        ignorProduct = self.IgnoreProduct(response)
        if ignorProduct == True:
            self.ProductIsOutofStock(GetterSetter.ProductUrl)
        shopify.productJson = json.loads(self.SetProductJson(response))
        category = shopify.GetCategory(self, response)
        name = self.GetName(response)
        if (re.search(r'\b' + 'Sale' + r'\b', category, re.IGNORECASE) or
            re.search(r'\b' + 'Dresses & Skirts' + r'\b', category, re.IGNORECASE) or
            re.search(r'\b' + 'New Arrivals' + r'\b', category, re.IGNORECASE)) \
                and not re.search(
            r'\b((shirt(dress?)|jump(suit?)|dress|romper|gown|suit|caftan)(s|es)?)\b', name, re.IGNORECASE):
            print('Skipping Non Dress Product')
            self.ProductIsOutofStock(GetterSetter.ProductUrl)
        else:
            self.GetProductInfo(response)
