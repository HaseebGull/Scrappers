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


class MadeTradeScrapper(shopify):
    Spider_BaseClass.testingGender = 'Women '
    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(MadeTradeScrapper, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        return spider

    def GetProductUrls(self, homePageResponse):
        # ========== Category And Subcategory ==========#
        topCategoryNodes = homePageResponse.xpath(
            "//nav[contains(@class,'Header__MainNav')]/ul/li[a[contains(text(),'New') or contains(text(),'Clothing') or contains(text(),'Sale')]]")
        for topCategoryNode in topCategoryNodes:
            topCategoryTitle = topCategoryNode.xpath("./a/text()").get().strip()
            topCategorylink = topCategoryNode.xpath("./a/@href").get()
            if not topCategorylink.startswith(store_url):
                topCategorylink = store_url.rstrip('/') + topCategorylink
            categoryNodes = topCategoryNode.xpath(
                "./div/div/div/a[contains(text(),'New') or contains(text(),'Women') or contains(text(),'Men') or contains(text(),'Kids')]")
            if not categoryNodes:
                category = topCategoryTitle
                self.listing(topCategorylink, category)
            else:
                for categoryNode in categoryNodes:
                    categoryTitle = categoryNode.xpath("./text()").get().strip()
                    categorylink = categoryNode.xpath("./@href").get()
                    if not categorylink.startswith(store_url):
                        categorylink = store_url.rstrip('/') + categorylink
                    if re.search('\?', categorylink):
                        categorylink = 'https' + categorylink.split('https' or 'http')[1].split('?')[0].strip()

                    subCategoryNodes = categoryNode.xpath(
                        "./following-sibling::ul/li/a[contains(text(),'Dress') or contains(text(),'Dress') or contains(text(),'Occasion') or contains(text(),'Jumpsuit') or contains(text(),'Baby Clothing')]")
                    for subCategoryNode in subCategoryNodes:
                        subCategoryTitle = subCategoryNode.xpath("./text()").get().strip()
                        subCategorylink = subCategoryNode.xpath("./@href").get()
                        if not subCategorylink.startswith(store_url):
                            subCategorylink = store_url.rstrip('/') + subCategorylink
                        # =================== BREADCRUM ===================3
                        category = topCategoryTitle + " " + categoryTitle + " " + subCategoryTitle
                        # ======================================#
                        self.listing(subCategorylink, category)
        return Spider_BaseClass.AllProductUrls

    def listing(self, categorylink, category):
        CategoryLinkResponse = requests.get(categorylink)
        collectionName = categorylink.split('/')[-1]
        categoryPageResponse = HtmlResponse(url=categorylink, body=CategoryLinkResponse.text, encoding='utf-8')
        url = 'https://n8xsq7.a.searchspring.io/api/search/search.json?userId=b8f4b768-587d-45d7-a889-0b100d817108' \
              '&domain=https%3A%2F%2Fwww.madetrade.com%2Fcollections%2F' + str(
            collectionName) + '%3Fpage%3D2&siteId=n8xsq7&page=1' \
                              '&bgfilter.collection_handle=' + str(
            collectionName) + '&redirectResponse=full&resultsFormat=native'
        responeapi = requests.get(url=url, timeout=6000)
        apiresponse = json.loads(responeapi.content)
        totalProducts = apiresponse['pagination']['totalResults']
        totalPages = 0
        pageNo = 1
        if totalProducts % 48 == 0:
            totalPages = totalProducts / 48
        else:
            totalPages = totalProducts / 48 + 1
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
                url = 'https://n8xsq7.a.searchspring.io/api/search/search.json?userId=b8f4b768-587d-45d7-a889-0b100d817108' \
                      '&domain=https%3A%2F%2Fwww.madetrade.com%2Fcollections%2F' + str(
                    collectionName) + '%3Fpage%3D2&siteId=n8xsq7&page=' + str(
                    pageNo) + '&bgfilter.collection_handle=' + str(
                    collectionName) + '&redirectResponse=full&resultsFormat=native'
                responeapi = requests.get(url=url)
                apiresponse = json.loads(responeapi.content)
            except:
                pass

    def GetProducts(self, response):
        ignorProduct = self.IgnoreProduct(response)
        if ignorProduct == True:
            self.ProductIsOutofStock(GetterSetter.ProductUrl)
        shopify.productJson = json.loads(self.SetProductJson(response))
        categoryAndName = shopify.GetCategory(self, response) + " " + self.GetName(response)
        if (re.search('Sale', categoryAndName, re.IGNORECASE) or
            re.search(r'\b' + 'New Arrivals' + r'\b', categoryAndName, re.IGNORECASE)) and not \
                re.search(r'\b((shirt(dress?)|jump(suit?)|dress|romper|gown|suit|caftan)(s|es)?)\b', categoryAndName,
                          re.IGNORECASE):
            print('Skipping Non Dress Product')
            self.ProductIsOutofStock(GetterSetter.ProductUrl)
        else:
            self.GetProductInfo(response)

    # def GetName(self, response):
    #     color = self.GetSelectedColor(response)
    #     name = shopify.GetName(self, response)
    #     if not color == '' and not re.search(color, name):
    #         name = name + ' - ' + color
    #     return name
    #
    # def GetSelectedColor(self, response):
    #     return response.xpath(
    #         "//fieldset/legend[@class='ProductForm__Label' and contains(text(),'Color')]/span/text()").get().strip()

    def IgnoreProduct(self, response):
        if re.search('"availability":', response.text):
            productAvailability = response.text.split('"availability":')[1].split(',')[0].strip()
            if not 'InStock' in productAvailability:
                return True
            else:
                return False
