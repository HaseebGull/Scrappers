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


class SuitsOutletsScrapper(shopify):
    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(SuitsOutletsScrapper, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        return spider

    def GetProductUrls(self, homePageResponse):
        # ========== Category And Subcategory ==========#
        topCategoryNodes = homePageResponse.xpath(
            "//nav[contains(@class,'Header__MainNav')]/ul/li[a[contains(text(),'SUITS') or contains(text(),'SALE')]]")
        for topCategoryNode in topCategoryNodes:
            topCategoryTitle = topCategoryNode.xpath("./a/text()").get().strip()
            topCategorylink = topCategoryNode.xpath("./a/@href").get()
            if not topCategorylink.startswith(store_url):
                topCategorylink = store_url.rstrip('/') + topCategorylink

            categoryNodes = topCategoryNode.xpath(
                "./div/div/div[a[contains(text(),'CATEGORY') or contains(text(),'DESIGN') or contains(text(),'OCCASION')]]")
            if not categoryNodes:
                category = "Men " + topCategoryTitle
                self.listing(topCategorylink, category)
            else:
                for categoryNode in categoryNodes:
                    categoryTitle = categoryNode.xpath("./a/text()").get().strip()
                    categorylink = categoryNode.xpath("./a/@href").get()
                    if not categorylink.startswith(store_url):
                        categorylink = store_url.rstrip('/') + categorylink
                    subCategoryNodes = categoryNode.xpath(
                        "./ul/li/a[not(contains(text(),'All')) and not(contains(text(),'Blazer')) and not(contains(text(),'Sequin'))]")
                    for subCategoryNode in subCategoryNodes:
                        subCategoryTitle = subCategoryNode.xpath("./text()").get().strip()
                        subCategorylink = subCategoryNode.xpath("./@href").get()
                        if not subCategorylink.startswith(store_url):
                            subCategorylink = store_url.rstrip('/') + subCategorylink

                        # =================== BREADCRUM ===================3
                        category = "Men " + topCategoryTitle + " " + categoryTitle + " " + subCategoryTitle
                        # ======================================#
                        self.listing(subCategorylink, category)
        return Spider_BaseClass.AllProductUrls

    def listing(self, categorylink, category):
        global rid, collectionFilter, collectionName
        # collectionName = categorylink.split("/")[-1]
        if re.search('collections', categorylink):
            collections = categorylink.split('collections/')[1]
            if '/' in collections:
                collectionName = collections.split('/')[0]
                collectionFilter = collections.split('/')[1]
            else:
                collectionName = collections
                collectionFilter = ''
        CategoryLinkResponse = requests.get(categorylink)
        CategoryLinkResponse = HtmlResponse(url=categorylink, body=CategoryLinkResponse.text, encoding='utf-8')

        if re.search('"rid":', CategoryLinkResponse.text):
            rid = CategoryLinkResponse.text.split('"rid":')[1].split('}')[0]
        apiUrl = 'https://www.searchanise.com/getresults?api_key=7m8s5V1K2C&q=&sortBy=sales_amount&sortOrder=desc' \
                 '&restrictBy[quantity]=1|&startIndex=0&maxResults=24&items=true&pages=true&categories=true' \
                 '&suggestions=true&queryCorrection=true&suggestionsMaxResults=3&pageStartIndex=0&pagesMaxResults=0' \
                 '&categoryStartIndex=0&categoriesMaxResults=0&facets=true&facetsShowUnavailableOptions=false' \
                 '&ResultsTitleStrings=5&ResultsDescriptionStrings=0&collection=' + str(
            collectionName) + '&collection_filter_tag' \
                              '=' + str(collectionFilter) + '&output=jsonp'

        responeapi = requests.get(url=apiUrl, timeout=6000)
        apiresponse = json.loads(responeapi.content)
        totalProducts = apiresponse['totalItems']
        totalPages = 0
        pageNo = 1
        startIndex = apiresponse['startIndex']
        if totalProducts % 24 == 0:
            totalPages = totalProducts / 40
        else:
            totalPages = totalProducts / 24 + 1
        while pageNo <= totalPages:
            pageNo += 1
            next_index = startIndex * pageNo
            for apiproducturl in apiresponse['items']:
                apiproducturl = store_url.rstrip('/') + apiproducturl['link']
                productUrl = self.GetCanonicalUrl(apiproducturl)
                print(productUrl)
                Spider_BaseClass.AllProductUrls.append(productUrl)
                siteMapCategory = str(Spider_BaseClass.ProductUrlsAndCategory.get(productUrl)).replace('None', '')
                if siteMapCategory:
                    Spider_BaseClass.ProductUrlsAndCategory[productUrl] = siteMapCategory + " " + category
                else:
                    Spider_BaseClass.ProductUrlsAndCategory[productUrl] = category
            try:
                apiUrl = 'https://www.searchanise.com/getresults?api_key=7m8s5V1K2C&q=&sortBy=sales_amount&sortOrder=desc' \
                         '&restrictBy[quantity]=1|&startIndex=' + str(
                    next_index) + '&maxResults=24&items=true&pages=true&categories=true' \
                                  '&suggestions=true&queryCorrection=true&suggestionsMaxResults=3&pageStartIndex=0&pagesMaxResults=0' \
                                  '&categoryStartIndex=0&categoriesMaxResults=0&facets=true&facetsShowUnavailableOptions=false' \
                                  '&ResultsTitleStrings=5&ResultsDescriptionStrings=0&collection=' + str(
                    collectionName) + '&collection_filter_tag' \
                                      '=' + str(collectionFilter) + '&output=jsonp'
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
        if (re.search('ON SALE', categoryAndName, re.IGNORECASE) or
            re.search('New Arrivals', categoryAndName, re.IGNORECASE)) and not \
                re.search(r'\b((shirt(dress?)|jump(suit?)|dress|gown|suit|suit set|caftan)(s|es)?)\b', categoryAndName,
                          re.IGNORECASE):
            print('Skipping Non Dress Product')
            self.ProductIsOutofStock(GetterSetter.ProductUrl)
        else:
            self.GetProductInfo(response)
