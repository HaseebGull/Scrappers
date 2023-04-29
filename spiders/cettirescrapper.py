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


class CettireScrapper(shopify):
    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(CettireScrapper, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        return spider

    def GetProductUrls(self, homePageResponse):
        # ========== Category And Subcategory ==========#
        # "//ul[@id='SiteNav']/li/a[contains(text(),'Women') or contains(text(),'Men') or contains(text(),'Kids')
        topCategoryNodes = homePageResponse.xpath(
            "//ul[@id='SiteNav']/li/a[contains(text(),'Women') or contains(text(),'Men') or contains(text(),'Kids')]")
        for topCategoryNode in topCategoryNodes:
            topCategoryTitle = topCategoryNode.xpath("./text()").get().strip()
            topCategorylink = topCategoryNode.xpath("./@href").get()
            if not topCategorylink.startswith(store_url):
                topCategorylink = store_url.rstrip('/') + topCategorylink
            print("TOP CATEGORY  :", topCategoryTitle, ": TOP CATEGORY LINK  :", topCategorylink)

            categoryNodes = topCategoryNode.xpath(
                "//ul[@id='SiteNavCache-" + str(
                    topCategoryTitle).lower() + "']/div/div[contains(@class,'has-list')]/div[h6/a[contains(text(),'Clothing') or contains(text(),'Baby') or contains(text(),'Girls') or contains(text(),'Boys')]]")
            for categoryNode in categoryNodes:
                categoryTitle = categoryNode.xpath("./h6/a/text()").get().strip()
                categorylink = categoryNode.xpath("./h6/a/@href").get()
                if not categorylink.startswith(store_url):
                    categorylink = store_url.rstrip('/') + categorylink
                print("CATEGORY  :", categoryTitle, ": CATEGORY LINK  :", categorylink)

                subCategoryNodes = categoryNode.xpath(
                    "./ul/li/a[not(contains(text(),'Polo')) and not(contains(text(),'T-Shirts')) and  contains(text(),'Shirts') or contains(text(),'Suits') or contains(text(),'Pants') or  contains(text(),'Dress') or contains(text(),'Jumpsuits') or contains(text(),'Clothing')]")
                if subCategoryNodes:
                    for subCategoryNode in subCategoryNodes:
                        subCategoryTitle = subCategoryNode.xpath("./text()").get().strip()
                        subCategorylink = subCategoryNode.xpath("./@href").get()
                        if not subCategorylink.startswith(store_url):
                            subCategorylink = store_url.rstrip('/') + subCategorylink
                        if topCategoryTitle == 'Women' and subCategoryTitle == 'Pants' or\
                                topCategoryTitle == 'Women' and subCategoryTitle == 'All Clothing':
                            continue
                        category = [topCategoryTitle, categoryTitle, subCategoryTitle]
                        print("SUB CATEGORY  :", subCategoryTitle, ":  SUB CATEGORY LINK  :", subCategorylink)
                        print("BreadCrum : ", category)
                        self.listing(subCategorylink, category)
        return Spider_BaseClass.AllProductUrls

    def listing(self, categorylink, category):
        KidsCategoryList = ['Dresses', 'Jumpsuits', 'Suits']
        categoryLinkResponse = requests.get(categorylink, stream=True)
        categoryLinkResponse = HtmlResponse(url=categorylink, body=categoryLinkResponse.text, encoding='utf-8')
        apiUrl = 'https://6l0oqj41cq-1.algolianet.com/1/indexes/*/queries?x-algolia-agent=Algolia%20for%20vanilla%20JavaScript%20(lite)%203.27.1%3Binstantsearch.js%201.12.1%3BJS%20Helper%202.26.0&x-algolia-application-id=6L0OQJ41CQ&x-algolia-api-key=ee556f77348dacc02278dafa57be6d34'
        body = '{"requests":[{"indexName":"dev_Cettire_date_desc","params":"query=&hitsPerPage=48&maxValuesPerFacet=20000&page=0&distinct=1&facets=%5B%22tags%22%2C%22Color%22%2C%22Size%22%2C%22vendor%22%2C%22product_type%22%5D&tagFilters=&facetFilters=%5B%22visibility%3AYES%22%2C%22department%3A' + str(
            category[0]).lower() + '%22%2C%22tags%3A' + category[
                  1] + '%22%2C%22tags%3A%22%2C%5B%22product_type%3A'+category[2]+'%22%5D%5D"}]}'
        responeapi = requests.post(url=apiUrl, data=body, timeout=6000)
        apiresponse = json.loads(responeapi.content)
        totalProducts = apiresponse['results'][0]['nbHits']
        pageNo = apiresponse['results'][0]['page']
        totalPages = apiresponse['results'][0]['nbPages']
        if totalProducts % 48 == 0:
            totalPages = totalProducts / 48
        else:
            totalPages = totalProducts / 48 + 1
        while pageNo <= totalPages:
            pageNo += 1
            for apiproducturl in apiresponse['results'][0]['hits']:
                apiproducturl = store_url + 'products/' + apiproducturl['handle']
                productUrl = self.GetCanonicalUrl(apiproducturl)
                print("PRODUCT URL :", productUrl)
                Spider_BaseClass.AllProductUrls.append(productUrl)
                siteMapCategory = str(Spider_BaseClass.ProductUrlsAndCategory.get(productUrl)).replace('None', '')
                if siteMapCategory:
                    Spider_BaseClass.ProductUrlsAndCategory[productUrl] = siteMapCategory + " " + ' '.join(category)
                else:
                    Spider_BaseClass.ProductUrlsAndCategory[productUrl] = ' '.join(category)
            # try:
            #     apiUrl = 'https://6l0oqj41cq-1.algolianet.com/1/indexes/*/queries?x-algolia-agent=Algolia%20for%20vanilla%20JavaScript%20(lite)%203.27.1%3Binstantsearch.js%201.12.1%3BJS%20Helper%202.26.0&x-algolia-application-id=6L0OQJ41CQ&x-algolia-api-key=ee556f77348dacc02278dafa57be6d34'
            #     body = '{"requests":[{"indexName":"dev_Cettire_date_desc","params":"query=&hitsPerPage=48&maxValuesPerFacet=20000&page=' + str(
            #         pageNo) + '&distinct=1&facets=%5B%22tags%22%2C%22Color%22%2C%22Size%22%2C%22vendor%22%2C%22product_type%22%5D&tagFilters=&facetFilters=%5B%22visibility%3AYES%22%2C%22department%3A' + \
            #            str(category[0]).lower() + '%22%2C%22tags%3A' + category[1] + '%22%2C%5B%22product_type%3A' + \
            #            category[2] + '%22%5D%5D"}]}'
            #     responeapi = requests.post(url=apiUrl, data=body, timeout=6000)
            #     apiresponse = json.loads(responeapi.content)
            # except:
            #     pass

    def GetName(self, response):
        pID = product_url.strip()[-6:]
        name = shopify.GetName(self, response)
        if not pID == '' and not re.search(pID, name):
            name = name + ' - ' + pID
        return name

    def IgnoreProduct(self, response):
        productAvailability = response.xpath("//link[@itemprop='availability']/@href").get()
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

    # def GetSizes(self, response):
    #     sizes = shopify.GetSizes(self, response)
    #     sizeList = []
    #     for size in sizes:
    #         mappedSize = size[1]
    #         if mappedSize in cettireSize_Dict:
    #             mappedSize = cettireSize_Dict[mappedSize]
    #         MappedSize = size[0], mappedSize, size[2], size[3], size[4], size[5]
    #         sizeList.append(MappedSize)
    #     return sizeList
