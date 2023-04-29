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


class FrameScrapper(shopify):
    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(FrameScrapper, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        return spider

    def GetProductUrls(self, homePageResponse):
        # ========== Category And Subcategory ==========#

        topCategoryNodes = homePageResponse.xpath(
            "//ul[@id='headerMenu']/li[a[contains(span/text(),'Women') or contains(span/text(),'Men') or contains(span/text(),'Sale')]]")
        for topCategoryNode in topCategoryNodes:
            topCategoryTitle = topCategoryNode.xpath("./a/span/text()").get().strip()
            topCategorylink = topCategoryNode.xpath("./a/@href").get()
            if not topCategorylink.startswith(store_url):
                topCategorylink = store_url.rstrip('/') + topCategorylink
            categoryNodes = topCategoryNode.xpath(
                "./div//ul/li[a[not(contains(text(),'All')) and contains(text(),'Clothing') or contains(text(),'Women')]]")
            for categoryNode in categoryNodes:
                categoryTitle = categoryNode.xpath("./a/text()").get().strip()
                categorylink = categoryNode.xpath("./a/@href").get()
                if not categorylink.startswith(store_url):
                    categorylink = store_url.rstrip('/') + categorylink
                subCategoryNodes = categoryNode.xpath(
                    "./following-sibling::li/a[contains(text(),'Dress') or contains(text(),'Shirts') or contains(text(),'Pants')]")
                for subCategoryNodes in subCategoryNodes:
                    subCategoryTitle = subCategoryNodes.xpath("./text()").get().strip()
                    if 'Women' in topCategoryTitle and subCategoryTitle == 'Pants':
                        continue
                    else:
                        subCategorylink = subCategoryNodes.xpath("./@href").get()
                        if not subCategorylink.startswith(store_url):
                            subCategorylink = store_url.rstrip('/') + subCategorylink
                        category = topCategoryTitle + " " + categoryTitle + " " + subCategoryTitle
                        self.listing(subCategorylink, category)
        return Spider_BaseClass.AllProductUrls

    def listing(self, categorylink, category):
        CategoryLinkResponse = requests.get(categorylink)
        CategoryLinkResponse = HtmlResponse(url=categorylink, body=CategoryLinkResponse.text, encoding='utf-8')
        pageNo = 1
        global rid
        if re.search('"rid":', CategoryLinkResponse.text):
            rid = CategoryLinkResponse.text.split('"rid":')[1].split('}')[0]
        apiUrl = 'https://xntojv.a.searchspring.io/api/search/search.json?resultsFormat=native&siteId=xntojv&page=' + str(
            pageNo) + '&bgfilter.collection_id=' + rid + ''
        responeapi = requests.get(url=apiUrl, timeout=6000)
        apiresponse = json.loads(responeapi.content)
        totalProducts = apiresponse['pagination']['totalResults']
        totalPages = 0
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
                apiUrl = 'https://xntojv.a.searchspring.io/api/search/search.json?resultsFormat=native&siteId=xntojv&page=' + str(
                    pageNo) + '&bgfilter.collection_id=' + rid + ''
                responeapi = requests.get(url=apiUrl)
                apiresponse = json.loads(responeapi.content)
            except:
                pass

    # def GetName(self, response):
    #     color = self.GetSelectedColor(response)
    #     name = shopify.GetName(self, response)
    #     if not color == '' and not re.search(color, name):
    #         name = name + ' - ' + color
    #     return name
    #
    # def GetSelectedColor(self, response):
    #     return response.xpath("//div[@class='swatch-header']/h6[@class='current-option']/text()").get().strip()

    def IgnoreProduct(self, response):
        if re.search('"availability":', response.text):
            productAvailability = response.text.split('"availability":')[1].split(',')[0].strip()
            if not 'InStock' in productAvailability:
                return True
            else:
                return False
