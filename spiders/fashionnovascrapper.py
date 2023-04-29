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


class FashionnovaScrapper(shopify):
    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(FashionnovaScrapper, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        return spider

    def GetProductUrls(self, homePageResponse):
        # ========== Category And Subcategory ==========#
        topCategoryNodes = homePageResponse.xpath(
            "//ul[@class='menu-brands__track']/li/a[text()='Women' or text()='Curve']")
        for topCategoryNode in topCategoryNodes:
            topCategoryTitle = topCategoryNode.xpath("./text()").get().strip()
            if topCategoryTitle == 'Curve':
                topCategoryTitle = 'Women ' + topCategoryTitle
            dataMenuBrandHandle = topCategoryNode.xpath("./@data-menu-brand-handle").get().strip()
            topCategorylink = topCategoryNode.xpath("./@href").get()
            if not topCategorylink.startswith(store_url):
                topCategorylink = store_url.rstrip('/') + topCategorylink
            topCategoryLinkResponse = requests.get(topCategorylink)
            topCategoryLinkResponse = HtmlResponse(url=topCategorylink, body=topCategoryLinkResponse.text,
                                                   encoding='utf-8')
            categoryNodes = topCategoryLinkResponse.xpath(
                "//nav[@data-menu-brand-handle='" + dataMenuBrandHandle + "']/ul[@data-menu-location='header']/li/a[contains(div/text(),'Dress') or contains(div/text(),'Sets') or contains(div/text(),'Jumpsuits') or contains(div/text(),'New In') or contains(div/text(),'Sale')]")
            for categoryNode in categoryNodes:
                categoryTitle = categoryNode.xpath("./div/text()").get().strip()
                categorylink = categoryNode.xpath("./@href").get()
                if not categorylink.startswith(store_url):
                    categorylink = store_url.rstrip('/') + categorylink
                # =================== BREADCRUM =================== #
                category = topCategoryTitle + " " + categoryTitle
                # ====================================== #
                self.listing(categorylink, category)
        return Spider_BaseClass.AllProductUrls

    def listing(self, categorylink, category):
        CategoryLinkResponse = requests.get(categorylink)
        categoryPageResponse = HtmlResponse(url=categorylink, body=CategoryLinkResponse.text, encoding='utf-8')
        global rid
        if re.search('"rid":', CategoryLinkResponse.text):
            rid = CategoryLinkResponse.text.split('"rid":')[1].split('}')[0]
        global collectionName
        if re.search('"collectionName":"', CategoryLinkResponse.text):
            collectionName = CategoryLinkResponse.text.split('"collectionName":"')[1].split('",')[0]
        url = 'https://xn5vepvd4i-2.algolianet.com/1/indexes/products/query?x-algolia-agent=Algolia%20for%20JavaScript%20(4.3.0)%3B%20Browser'
        queryString = '{"query":"","userToken":"anonymous-a6fd9747-7e02-448c-90ce-6e6420e9d875","ruleContexts":["collection","' + str(
            collectionName) + '"],"analyticsTags":["collection","' + str(
            collectionName) + '","desktop","Returning","Pakistan"],"clickAnalytics":true,"distinct":1,"page":0,"hitsPerPage":48,"facetFilters":["collections:' + str(
            collectionName) + '"],"facetingAfterDistinct":true,"attributesToRetrieve":["handle","image","title"],"personalizationImpact":0}'
        headers = {"x-algolia-api-key": "0e7364c3b87d2ef8f6ab2064f0519abb", "x-algolia-application-id": "XN5VEPVD4I"}
        responeapi = requests.post(url=url, data=queryString, headers=headers, timeout=6000)
        apiresponse = json.loads(responeapi.content)
        totalProducts = apiresponse['nbHits']
        pageNo = apiresponse['page']
        totalPages = apiresponse['nbPages']
        if totalProducts % 48 == 0:
            totalPages = totalProducts / 48
        else:
            totalPages = totalProducts / 48 + 1
        while pageNo <= totalPages:
            pageNo += 1
            for apiproducturl in apiresponse['hits']:
                apiproducturl = store_url + 'products/' + apiproducturl['handle']
                productUrl = self.GetCanonicalUrl(apiproducturl)
                Spider_BaseClass.AllProductUrls.append(productUrl)
                siteMapCategory = str(Spider_BaseClass.ProductUrlsAndCategory.get(productUrl)).replace('None', '')
                if siteMapCategory:
                    Spider_BaseClass.ProductUrlsAndCategory[productUrl] = siteMapCategory + " " + category
                else:
                    Spider_BaseClass.ProductUrlsAndCategory[productUrl] = category
            try:
                url = 'https://xn5vepvd4i-2.algolianet.com/1/indexes/products/query?x-algolia-agent=Algolia%20for%20JavaScript%20(4.3.0)%3B%20Browser'
                queryString = '{"query":"","userToken":"anonymous-a6fd9747-7e02-448c-90ce-6e6420e9d875","ruleContexts":["collection","' + str(
                    collectionName) + '"],"analyticsTags":["collection","' + str(
                    collectionName) + '","desktop","Returning","Pakistan"],"clickAnalytics":true,"distinct":1,"page":' + str(
                    pageNo) + ',"hitsPerPage":48,"facetFilters":["collections:' + str(
                    collectionName) + '"],"facetingAfterDistinct":true,"attributesToRetrieve":["handle","image","title"],"personalizationImpact":0}'
                headers = {"x-algolia-api-key": "0e7364c3b87d2ef8f6ab2064f0519abb",
                           "x-algolia-application-id": "XN5VEPVD4I"}
                responeapi = requests.post(url=url, data=queryString, headers=headers, timeout=6000)
                apiresponse = json.loads(responeapi.content)
            except:
                pass

    def GetProducts(self, response):
        ignorProduct = self.IgnoreProduct(response)
        if ignorProduct == True:
            self.ProductIsOutofStock(GetterSetter.ProductUrl)
        shopify.productJson = json.loads(self.SetProductJson(response))
        categoryAndName = shopify.GetCategory(self, response) + " " + self.GetName(response)
        if (re.search('sale', categoryAndName, re.IGNORECASE) or
            re.search('new in', categoryAndName, re.IGNORECASE)) \
                and not re.search('dress', categoryAndName, re.IGNORECASE) and not re.search(
            r'\b((shirt(dress?)|jump(suit?)|dress|set|romper|gown|suit|caftan)(s|es)?)\b', categoryAndName, re.IGNORECASE):
            print('Skipping Non Dress Product')
            self.ProductIsOutofStock(GetterSetter.ProductUrl)
        else:
            self.GetProductInfo(response)

    def SetProductJson(self, response):
        productJsonStr = requests.get(GetterSetter.ProductUrl + '.js',
                                      cookies=Spider_BaseClass.cookiesDict).content
        return productJsonStr

    def GetName(self, response):
        color = self.GetSelectedColor(response)
        name = shopify.GetName(self, response)
        if not color == '' and not re.search(color, name):
            name = name + ' - ' + color
        return name

    def GetSelectedColor(self, response):
        return response.xpath("//p[@class='product-info__color-name']/text()").get().strip()

    def GetSizes(self, response):
        sizeList = []
        sizes = shopify.GetSizes(self, response)
        color = self.GetSelectedColor(response)
        for size in sizes:
            sizeList.append([color, size[1], size[2], size[3], size[4], size[5]])
        return sizeList

    def IgnoreProduct(self, response):
        if re.search('"availability":', response.text):
            productAvailability = response.text.split('"availability":')[1].split(',')[0].strip()
            if not 'InStock' in productAvailability:
                return True
            else:
                return False
