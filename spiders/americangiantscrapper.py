import sys
from pathlib import Path

DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(DIR.parent.parent.parent.parent))
__package__ = DIR.name

import django

django.setup()
from Shopify import *
from BaseClass import Spider_BaseClass
from scrapy import signals

store_url = sys.argv[4]


class AmericanGiantScrapper(shopify):
    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(AmericanGiantScrapper, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        return spider

    def GetProductUrls(self, homePageResponse):
        # ========== Category And Subcategory ==========#
        topCategoryNodes = homePageResponse.xpath(
            "//nav[contains(@class,'header-main__megamenu ')]/div/div[button[contains(text(),'Women') or contains(text(),'Men')]]")
        for topCategoryNode in topCategoryNodes:
            topCategoryTitle = topCategoryNode.xpath("./button/text()").get()
            categoryNodes = topCategoryNode.xpath(
                ".//div[contains(@class,'megamenu__list')][div/a[contains(span/text(),'Bottoms')]]")
            for categoryNode in categoryNodes:
                categoryTitle = categoryNode.xpath("./div/a/span/text()").get()
                categorylink = categoryNode.xpath("./div/a/@href").get()
                if not categorylink.startswith(store_url):
                    categorylink = store_url.rstrip('/') + categorylink
                subCategoryNodes = categoryNode.xpath("./ul/li/a[contains(span/text(),'Dress')]")
                for subCategoryNode in subCategoryNodes:
                    subCategoryTitle = subCategoryNode.xpath("./span/text()").get()
                    subcategorylink = subCategoryNode.xpath("./@href").get()
                    if not subcategorylink.startswith(store_url):
                        subcategorylink = store_url.rstrip('/') + subcategorylink
                    category = topCategoryTitle + " " + categoryTitle + " " + subCategoryTitle
                    self.listing(subcategorylink, category)
        return Spider_BaseClass.AllProductUrls

    def listing(self, subcategorylink, category):
        subCategoryLinkResponse = requests.get(subcategorylink)
        subCategoryLinkResponse = HtmlResponse(url=subcategorylink, body=subCategoryLinkResponse.text, encoding='utf-8')
        global rid
        if re.search('"rid":', subCategoryLinkResponse.text):
            rid = subCategoryLinkResponse.text.split('"rid":')[1].split('}')[0]
        apiUrl = 'https://jgzmac.a.searchspring.io/api/search/search.json?domain=%2Fcollections%2Fwomens-dresses&siteId=jgzmac&resultsFormat=native&resultsPerPage=100&userId=652cf60e410f42a8af841c6df72c37df&bgfilter.ss_exclude=0&bgfilter.collection_id=' + str(
            rid) + ''
        responeapi = requests.get(url=apiUrl, timeout=6000)
        apiresponse = json.loads(responeapi.content)
        totalProducts = apiresponse['pagination']['totalResults']
        totalPages = 0
        pageNo = 1
        if totalProducts % 40 == 0:
            totalPages = totalProducts / 40
        else:
            totalPages = totalProducts / 40 + 1
        while pageNo <= totalPages:
            pageNo += 1
            for apiproducturl in apiresponse['results']:
                apiproducturl = store_url + 'products/' + apiproducturl['handle']
                productUrl = self.GetCanonicalUrl(apiproducturl)
                Spider_BaseClass.AllProductUrls.append(productUrl)

                siteMapCategory = str(Spider_BaseClass.ProductUrlsAndCategory.get(productUrl)).replace('None', '')
                if siteMapCategory:
                    Spider_BaseClass.ProductUrlsAndCategory[productUrl] = siteMapCategory + " " + category
                else:
                    Spider_BaseClass.ProductUrlsAndCategory[productUrl] = category
            try:
                apiUrl = 'https://jgzmac.a.searchspring.io/api/search/search.json?domain=%2Fcollections%2Fwomens-dresses&siteId=jgzmac&resultsFormat=native&resultsPerPage=100&userId=652cf60e410f42a8af841c6df72c37df&bgfilter.ss_exclude=0&bgfilter.collection_id=' + str(
                    rid) + '&page=' + str(pageNo) + ''
                responeapi = requests.get(url=apiUrl)
                apiresponse = json.loads(responeapi.content)
            except:
                pass

    # def GetName(self, response):
    #     color = self.GetSelectedColor(response)
    #     name = shopify.GetName(self, response)
    #     if not color == '' and not re.search(color, name):
    #         name = name + '-' + color
    #     return name
    #
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
