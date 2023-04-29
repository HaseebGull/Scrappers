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


class RedDressScrapper(shopify):
    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(RedDressScrapper, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        return spider

    def GetProductUrls(self, homePageResponse):
        # ========== Category And Subcategory ==========#
        topCategoryNodes = homePageResponse.xpath(
            """//nav/ul/li[div/span/a[contains(text(),'Clothing') or contains(text(),'Sale') or contains(text(),"What's New")]]""")
        for topCategoryNode in topCategoryNodes:
            topCategoryTitle = topCategoryNode.xpath("./div/span/a/text()").get().strip()
            topCategorylink = topCategoryNode.xpath("./div/span/a/@href").get()
            if not topCategorylink.startswith(store_url):
                topCategorylink = store_url.rstrip('/') + topCategorylink

            categoryNodes = topCategoryNode.xpath(
                "./ul/li[div/span/a[contains(text(),'Dress') or contains(text(),'Trending') or contains(text(),'Swim') or contains(text(),'Play') or contains(text(),'Tops') or contains(text(),'On Sale')]]")
            for categoryNode in categoryNodes:
                categoryTitle = categoryNode.xpath("./div/span/a/text()").get().strip()
                categorylink = categoryNode.xpath("./div/span/a/@href").get()
                if not categorylink.startswith(store_url):
                    categorylink = store_url.rstrip('/') + categorylink

                subCategoryNodes = categoryNode.xpath(
                    "./ul/li/div/span/a[not(contains(text(),'All'))  and contains(text(),'Dress')  or contains(text(),'Bodysuits')  or contains(text(),'Romper')  or contains(text(),'Jumpsuits') or contains(text(),'Cover') or contains(text(),'One')]")
                for subCategoryNode in subCategoryNodes:
                    subCategoryTitle = subCategoryNode.xpath("./text()").get().strip()
                    subCategorylink = subCategoryNode.xpath("./@href").get()
                    if not subCategorylink.startswith(store_url):
                        subCategorylink = store_url.rstrip('/') + subCategorylink

                    # =================== BREADCRUM =================== #
                    category = 'Women ' + topCategoryTitle + " " + categoryTitle + " " + subCategoryTitle
                    # ======================================#
                    self.listing(subCategorylink, category)
        return Spider_BaseClass.AllProductUrls

    def listing(self, categorylink, category):
        CategoryLinkResponse = requests.get(categorylink)
        collectionName = categorylink.split('/')[-1]
        categoryPageResponse = HtmlResponse(url=categorylink, body=CategoryLinkResponse.text, encoding='utf-8')
        url = 'https://a53rh3.a.searchspring.io/api/search/search.json?ajaxCatalog=v3&resultsFormat=native&siteId' \
              '=a53rh3&domain=https%3A%2F%2Fwww.reddress.com%2Fcollections%2F' + str(
            collectionName) + '&bgfilter.collection_handle=' + str(
            collectionName) + '&bgfilter.is_published=yes&q=&page=1&userId=V3-527BAA9F-2509-41D0-B469-081C80DDE16B '
        responeapi = requests.get(url=url, timeout=6000)
        apiresponse = json.loads(responeapi.content)
        totalProducts = apiresponse['pagination']['totalResults']
        totalPages = 0
        pageNo = 1
        if totalProducts % 24 == 0:
            totalPages = totalProducts / 24
        else:
            totalPages = totalProducts / 24 + 1
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
                url = 'https://a53rh3.a.searchspring.io/api/search/search.json?ajaxCatalog=v3&resultsFormat=native&siteId=a53rh3&domain=https%3A%2F%2Fwww.reddress.com%2Fcollections%2F' + str(
                    collectionName) + '&bgfilter.collection_handle=' + str(
                    collectionName) + '&bgfilter.is_published=yes&q=&page=' + str(
                    pageNo) + '&userId=V3-527BAA9F-2509-41D0-B469-081C80DDE16B'
                responeapi = requests.get(url=url)
                apiresponse = json.loads(responeapi.content)
            except:
                pass

    def IgnoreProduct(self, response):
        if re.search('"availability":', response.text):
            productAvailability = response.text.split('"availability":')[1].split(',')[0].strip()
            if not 'InStock' in productAvailability:
                return True
            else:
                return False
