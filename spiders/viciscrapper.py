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


class ViciScrapper(shopify):
    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(ViciScrapper, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        return spider
    # //ul[contains(@class,'site-navigation')]/li[a[ contains(text(),'Clothing') or contains(text(),'Sale')]]/div[contains(ul/@class,'site-nav__dropdown-list') or contains(div/@class,'site-nav__container')]/div/div/div/div/a[contains(text(),'Jeans')]
    def GetProductUrls(self, homePageResponse):
        # ========== Category And Subcategory ==========#
        topCategoryNodes = homePageResponse.xpath(
            "//ul[contains(@class,'site-navigation')]/li[a[contains(text(),'New') or contains(text(),'Clothing') or contains(text(),'Dresses') or contains(text(),'Sale')]]")
        for topCategoryNode in topCategoryNodes:
            topCategoryTitle = topCategoryNode.xpath("./a/text()").get().strip()
            topCategorylink = topCategoryNode.xpath("./a/@href").get()
            if not topCategorylink.startswith(store_url):
                topCategorylink = store_url.rstrip('/') + topCategorylink
            categoryNodes = topCategoryNode.xpath(
                "./div[contains(ul/@class,'site-nav__dropdown-list') or contains(div/@class,'site-nav__container')]/div/div/div/div/a[contains(text(),'Dress') and not(contains(text(),'All')) or contains(text(),'Bodysuit') or contains(text(),'Rompers') or contains(text(),'Babydoll') or contains(text(),'Bodycon') or contains(text(),'Sundresses') or contains(text(),'Bridal') or contains(text(),'Bump Friendly') or contains(text(),'Resort Ready') or contains(text(),'Special Event') or contains(text(),'Work To Weekend') ]")
            if not categoryNodes:
                category = 'Women ' + topCategoryTitle
                self.listing(topCategorylink, category)
            else:
                for categoryNode in categoryNodes:
                    categoryTitle = categoryNode.xpath("./text()").get().strip()
                    categorylink = categoryNode.xpath("./@href").get()
                    if not categorylink.startswith(store_url):
                        categorylink = store_url.rstrip('/') + categorylink
                    if re.search('\?', categorylink):
                        categorylink = 'https' + categorylink.split('https' or 'http')[1].split('?')[0].strip()
                    # =================== BREADCRUM ===================3
                    category = 'Women ' + topCategoryTitle + " " + categoryTitle
                    # ======================================#
                    self.listing(categorylink, category)
        return Spider_BaseClass.AllProductUrls

    def listing(self, categorylink, category):
        CategoryLinkResponse = requests.get(categorylink)
        CategoryLinkResponse = HtmlResponse(url=categorylink, body=CategoryLinkResponse.text, encoding='utf-8')

        global rid
        if re.search('"rid":', CategoryLinkResponse.text):
            rid = CategoryLinkResponse.text.split('"rid":')[1].split('}')[0]
        collectionName = categorylink.split("/")[-1]
        apiUrl = 'https://2pp9yv.a.searchspring.io/api/search/search.json?domain=%2Fcollections%2F' + str(
            collectionName) + '&userId=4yioB6JRdvdkQ4tEg5u8GYl4GQIZhCTBex2GT51DgrN47e0JV2&siteId=2pp9yv&resultsFormat' \
                              '=native&resultsPerPage=48&bgfilter.collection_id=' + str(
            rid) + '&bgfilter.ss_timestamp.high=1654153390&page=1'
        responeapi = requests.get(url=apiUrl, timeout=6000)
        apiresponse = json.loads(responeapi.content)
        totalProducts = apiresponse['pagination']['totalResults']
        totalPages = apiresponse['pagination']['totalPages']
        pageNo = apiresponse['pagination']['currentPage']
        # if totalProducts % 40 == 0:
        #     totalPages = totalProducts / 40
        # else:
        #     totalPages = totalProducts / 40 + 1
        while pageNo <= totalPages:
            pageNo += 1
            for apiproducturl in apiresponse['results']:
                apiproducturl = store_url.rstrip('/') + apiproducturl['url']
                productUrl = self.GetCanonicalUrl(apiproducturl)
                Spider_BaseClass.AllProductUrls.append(productUrl)
                siteMapCategory = str(Spider_BaseClass.ProductUrlsAndCategory.get(productUrl)).replace('None', '')
                if siteMapCategory:
                    Spider_BaseClass.ProductUrlsAndCategory[productUrl] = siteMapCategory + " " + category
                else:
                    Spider_BaseClass.ProductUrlsAndCategory[productUrl] = category
            try:
                apiUrl = 'https://2pp9yv.a.searchspring.io/api/search/search.json?domain=%2Fcollections%2F' + str(
                    collectionName) + '&userId=4yioB6JRdvdkQ4tEg5u8GYl4GQIZhCTBex2GT51DgrN47e0JV2&siteId=2pp9yv&resultsFormat=native&resultsPerPage=48&bgfilter.collection_id=' + str(
                    rid) + '&bgfilter.ss_timestamp.high=1654153390&page=' + str(pageNo) + ''
                responeapi = requests.get(url=apiUrl)
                apiresponse = json.loads(responeapi.content)
            except:
                pass

    def GetProducts(self, response):
        ignorProduct = self.IgnoreProduct(response)
        if ignorProduct == True:
            self.ProductIsOutofStock(GetterSetter.ProductUrl)
        shopify.productJson = json.loads(self.SetProductJson(response))
        categoryAndName = shopify.GetCategory(self, response) + " " + self.GetName(response)
        if (re.search(r'\b' + 'Sale' + r'\b', categoryAndName, re.IGNORECASE) or
            re.search(r'\b' + "What's New" + r'\b', categoryAndName, re.IGNORECASE)) and not \
                re.search(r'\b((shirt(dress?)|jump(suit?)|dress|gown|romper|suit|caftan)(s|es)?)\b', categoryAndName,
                          re.IGNORECASE):
            print('Skipping Non Dress Product')
            self.ProductIsOutofStock(GetterSetter.ProductUrl)
        else:
            self.GetProductInfo(response)

    def IgnoreProduct(self, response):
        if re.search('"availability":', response.text):
            productAvailability = response.text.split('"availability":')[1].split(',')[0].strip()
            if not 'InStock' in productAvailability:
                return True
            else:
                return False
