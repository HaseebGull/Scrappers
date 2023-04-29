import sys
from pathlib import Path
from SiteSizesDict import *
DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(DIR.parent.parent.parent.parent))
__package__ = DIR.name

import django

django.setup()
from Shopify import *
from BaseClass import Spider_BaseClass
from scrapy import signals

store_url = sys.argv[4]


class ParlourXScrapper(shopify):
    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(ParlourXScrapper, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        return spider

    def GetProductUrls(self, homePageResponse):
        # ========== Category And Subcategory ==========#
        topCategoryNodes = homePageResponse.xpath(
            "(//ul[contains(@class,'site-nav')])[1]/li[a[contains(text(),'New') or contains(span/text(),'Style') or contains(text(),'Sale')]]")
        for topCategoryNode in topCategoryNodes:
            if topCategoryNode.xpath("./a/span/text()").get() == None:
                topCategoryNodeTitle = topCategoryNode.xpath("./a/text()").get()
            else:
                topCategoryNodeTitle = topCategoryNode.xpath("./a/span/text()").get()
            topCategoryNodelink = topCategoryNode.xpath("./a/@href").get()
            if not topCategoryNodelink.startswith(store_url):
                topCategoryNodelink = store_url.rstrip('/') + topCategoryNodelink
            print("TOP CATEGORY  :", topCategoryNodeTitle)
            print("TOP CATEGORY LINK  :", topCategoryNodelink)

            topcategoryLinkResponse = requests.get(topCategoryNodelink)
            topcategoryLinkResponse = HtmlResponse(url=topCategoryNodelink, body=topcategoryLinkResponse.text,
                                                   encoding='utf-8')

            categoryNodes = topcategoryLinkResponse.xpath(
                "//ul[contains(@class,'collection-listing')]/li/a[contains(span/text(),'DRESSES') or contains(span/text(),'JUMPSUITS') or contains(text(),'jumpsuits')]")
            if not categoryNodes:
                categoryNodes = topcategoryLinkResponse.xpath(
                    "//div[@data-tag-prefix='Style_']/div/a[contains(text(),'Dress') or contains(text(),'JUMPSUITS') or contains(text(),'jumpsuits')]")
            for categoryNode in categoryNodes:
                if categoryNode.xpath("./span/text()").get() == None:
                    categoryNodeTitle = categoryNode.xpath("./text()").get()
                else:
                    categoryNodeTitle = categoryNode.xpath("./span/text()").get()

                categoryNodelink = categoryNode.xpath("./@href").get()
                if not categoryNodelink.startswith(store_url):
                    categoryNodelink = store_url.rstrip('/') + categoryNodelink
                print("CATEGORY  :", categoryNodeTitle)
                print("CATEGORY LINK  :", categoryNodelink)
                category = topCategoryNodeTitle + " " + categoryNodeTitle
                self.listing(categoryNodelink, category)
        return Spider_BaseClass.AllProductUrls

    def listing(self, categorylink, category):
        categoryLinkResponse = requests.get(categorylink)
        categoryLinkResponse = HtmlResponse(url=categorylink, body=categoryLinkResponse.text, encoding='utf-8')
        product_list = categoryLinkResponse.xpath(
            "//a[contains(@class,'o-product-thumbnail__details')]/@href").extract()
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

    # def GetName(self, response):
    #     color = self.GetSelectedColor(response)
    #     name = shopify.GetName(self, response)
    #     if not color == '' and not re.search(color, name):
    #         name = name + '-' + color
    #     return name

    # def GetSelectedColor(self, response):
    #     return response.xpath(
    #         "//div[@class='swatch clearfix'][div[@class='header' and contains(text(),'Color')]]/div/div/text()").get().strip()

    def IgnoreProduct(self, response):
        if re.search('"availability":', response.text):
            productAvailability = response.text.split('"availability":')[1].split(',')[0].strip()
            if not 'InStock' in productAvailability:
                return True
            else:
                return False

    def GetCategory(self, response):
        filterList = []
        if GetterSetter.ProductUrl in Spider_BaseClass.ProductUrlsAndCategory:
            categories = Spider_BaseClass.ProductUrlsAndCategory[GetterSetter.ProductUrl]
            for category in str(categories).split('$'):
                filterList.append(category)

        for filter in shopify.productJson['tags']:
            filterList.append(filter)
        filters = '$'.join(map(str, filterList))
        return 'Women ' + filters

    def GetSizes(self, response):
        sizes = shopify.GetSizes(self, response)
        sizeList = []
        for size in sizes:
            mappedSize = size[1]
            MappedSize = size[0], mappedSize, size[2], size[3], size[4], size[5]
            sizeList.append(MappedSize)
        return sizeList