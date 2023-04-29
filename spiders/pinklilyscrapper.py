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


class PinkLilyScrapper(shopify):
    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(PinkLilyScrapper, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        return spider

    def GetProductUrls(self, homePageResponse):
        # ========== Category And Subcategory ==========#
        global topCategorylink
        topCategoryNodes = homePageResponse.xpath(
            "//nav[@id='AccessibleNav']/ul/li[contains(button/span/text(),'New') or contains(button/span/text(),'Clothing') or contains(button/span/text(),'Dress')  or contains(a/span/text(),'Sale')]")
        for topCategoryNode in topCategoryNodes:
            topCategoryTitle = topCategoryNode.xpath("./button/span/text()")
            if not topCategoryTitle:
                print('sale top')
                topCategoryTitle = topCategoryNode.xpath("./a/span/text()").get().strip()
                print(topCategoryTitle)
                topCategorylink = topCategoryNode.xpath("./a/@href").get()
                print(topCategorylink)
                if not topCategorylink.startswith(store_url):
                    topCategorylink = store_url.rstrip('/') + topCategorylink
            else:
                topCategoryTitle = topCategoryTitle.get().strip()
            categoryNodes = topCategoryNode.xpath(
                "./div/div/ul/li[a[contains(span/text(),'Dress') and not(contains(span/text(),'All')) or contains(span/text(),'Romper') or contains(span/text(),'Bridal Shop') or contains(span/text(),'New Arrivals')]]")
            if not categoryNodes:
                category = topCategoryTitle
                self.listing(topCategorylink, category)
            else:
                for categoryNode in categoryNodes:
                    categoryTitle = categoryNode.xpath("./a/span/text()").get().strip()
                    categorylink = categoryNode.xpath("./a/@href").get()
                    if not categorylink.startswith(store_url):
                        categorylink = store_url.rstrip('/') + categorylink
                    subCategoryNodes = categoryNode.xpath("./ul/li/a")
                    if not subCategoryNodes:
                        category = topCategoryTitle + " " + categoryTitle
                        self.listing(categorylink, category)
                    else:
                        for subCategoryNode in subCategoryNodes:
                            subCategoryTitle = subCategoryNode.xpath("./span/text()").get().strip()
                            subCategorylink = subCategoryNode.xpath("./@href").get()
                            if not subCategorylink.startswith(store_url):
                                subCategorylink = store_url.rstrip('/') + subCategorylink
                            if topCategoryTitle == 'Clothing' and categoryTitle == 'Bridal Shop':
                                continue
                            else:
                                # =================== BREADCRUM =================== #
                                category = topCategoryTitle + " " + categoryTitle + " " + subCategoryTitle
                                # ======================================#
                                self.listing(subCategorylink, category)
        return Spider_BaseClass.AllProductUrls

    def listing(self, categorylink, category):
        CategoryLinkResponse = requests.get(categorylink)
        CategoryLinkResponse = HtmlResponse(url=categorylink, body=CategoryLinkResponse.text, encoding='utf-8')

        global rid
        if re.search('"rid":', CategoryLinkResponse.text):
            rid = CategoryLinkResponse.text.split('"rid":')[1].split('}')[0]
        collectionName = categorylink.split("/")[-1]
        apiUrl = 'https://diqax0.a.searchspring.io/api/search/search.json?userId=744b2ea9-1dc6-4180-a827-9e04f902d52d&domain=https%3A%2F%2Fpinklily.com%2Fcollections%2F' + str(
            collectionName) + '%3Fpage%3D2&siteId=diqax0&page=1&bgfilter.ss_is_published=yes&bgfilter.collection_id=' + str(
            rid) + '&resultsFormat=native'
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
                apiUrl = 'https://diqax0.a.searchspring.io/api/search/search.json?userId=744b2ea9-1dc6-4180-a827-9e04f902d52d&domain=https%3A%2F%2Fpinklily.com%2Fcollections%2F' + str(
                    collectionName) + '%3Fpage%3D2&siteId=diqax0&page='+str(pageNo)+'&bgfilter.ss_is_published=yes&bgfilter.collection_id=' + str(
                    rid) + '&resultsFormat=native'
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
        if (re.search(r'\b' + 'Sale!' + r'\b', categoryAndName, re.IGNORECASE) or
            re.search(r'\b' + "New" + r'\b', categoryAndName, re.IGNORECASE)) and not \
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
