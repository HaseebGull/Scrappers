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


class MarissaCollectionsScrapper(shopify):
    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(MarissaCollectionsScrapper, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        return spider

    def GetProductUrls(self, homePageResponse):
        # ========== Category And Subcategory ==========#
        topCategoryNodes = homePageResponse.xpath(
            "//nav[@class='main-nav']/ul/li[a[contains(span/text(),'women') or contains(span/text(),'new')]]")
        for topCategoryNode in topCategoryNodes:
            topCategoryTitle = topCategoryNode.xpath("./a/span/text()").get().strip()
            topCategorylink = topCategoryNode.xpath("./a/@href").get()
            if not topCategorylink.startswith(store_url):
                topCategorylink = store_url.rstrip('/') + topCategorylink
            categoryNodes = topCategoryNode.xpath(
                "./div/div/dl[dt/a[contains(span/text(),'CLOTHING') or contains(span/text(),'new')]]")
            for categoryNode in categoryNodes:
                categoryTitle = categoryNode.xpath("./dt/a/span/text()").get().strip()
                categorylink = categoryNode.xpath("./dt/a/@href").get()
                if not categorylink.startswith(store_url):
                    categorylink = store_url.rstrip('/') + categorylink
                if re.search('\?', categorylink):
                    categorylink = 'https' + categorylink.split('https' or 'http')[1].split('?')[0].strip()
                subcategoryNodes = categoryNode.xpath(
                    "./dd/a[contains(text(),'DRESSES') or contains(text(),'latest arrivals')]")
                for subcategoryNode in subcategoryNodes:
                    subcategoryTitle = subcategoryNode.xpath("./text()").get().strip()
                    subcategoryLink = subcategoryNode.xpath("./@href").get()
                    if not subcategoryLink.startswith(store_url):
                        subcategoryLink = store_url.rstrip('/') + subcategoryLink
                    if re.search('\?', subcategoryLink):
                        subcategoryLink = 'https' + subcategoryLink.split('https' or 'http')[1].split('?')[0].strip()
                    category = [topCategoryTitle, categoryTitle, subcategoryTitle]
                    self.listing(subcategoryLink, category)
        return Spider_BaseClass.AllProductUrls

    def listing(self, subcategorylink, category):
        collection = subcategorylink.rsplit('/')[-1]
        subCategoryLinkResponse = requests.get(subcategorylink)
        subCategoryLinkResponse = HtmlResponse(url=subcategorylink, body=subCategoryLinkResponse.text, encoding='utf-8')
        global rid
        if re.search('"rid":', subCategoryLinkResponse.text):
            rid = subCategoryLinkResponse.text.split('"rid":')[1].split('}')[0]
        if category[0] == 'women':
            apiUrl = 'https://744hg4.a.searchspring.io/api/search/search.json?ajaxCatalog=v3&resultsFormat=native&siteId=744hg4&domain=https%3A%2F%2Fmarissacollections.com%2Fcollections%2F' + str(
                collection) + '&bgfilter.collection_id=' + rid + '&bgfilter.ss_category=' + str(
                category[0]).capitalize() + '%3E' + str(category[1]).capitalize() + '%3E' + str(
                category[2]).capitalize() + '&q=&page=1'
        else:
            apiUrl = 'https://744hg4.a.searchspring.io/api/search/search.json?ajaxCatalog=v3&resultsFormat=native&siteId=744hg4&domain=https%3A%2F%2Fmarissacollections.com%2Fcollections%2F' + str(
                collection) + '&bgfilter.collection_id=' + rid + '&bgfilter.ss_category=' + str(
                category[0]).capitalize() + '%27s%3E' + str(category[2]).capitalize() + '&q=&page=1'
        apiRespone = requests.get(url=apiUrl, timeout=6000)
        apiJson = json.loads(apiRespone.content)
        totalProducts = apiJson['pagination']['totalResults']
        totalPages = 0
        pageNo = 1
        if totalProducts % 60 == 0:
            totalPages = totalProducts / 60
        else:
            totalPages = totalProducts / 60 + 1
        while pageNo <= totalPages:
            pageNo += 1
            for apiproducturl in apiJson['results']:
                apiproducturl = store_url + 'products/' + apiproducturl['handle']
                productUrl = self.GetCanonicalUrl(apiproducturl)
                Spider_BaseClass.AllProductUrls.append(productUrl)
                siteMapCategory = str(Spider_BaseClass.ProductUrlsAndCategory.get(productUrl)).replace('None', '')
                if siteMapCategory:
                    Spider_BaseClass.ProductUrlsAndCategory[productUrl] = siteMapCategory + " " + category
                else:
                    Spider_BaseClass.ProductUrlsAndCategory[productUrl] = category
            try:
                if category[0] == 'women':
                    apiUrl = 'https://744hg4.a.searchspring.io/api/search/search.json?ajaxCatalog=v3&resultsFormat=native&siteId=744hg4&domain=https%3A%2F%2Fmarissacollections.com%2Fcollections%2F' + str(
                        collection) + '&bgfilter.collection_id=' + rid + '&bgfilter.ss_category=' + str(
                        category[0]).capitalize() + '%3E' + str(category[1]).capitalize() + '%3E' + str(
                        category[2]).capitalize() + '&q=&page=' + str(pageNo) + ''
                else:
                    apiUrl = 'https://744hg4.a.searchspring.io/api/search/search.json?ajaxCatalog=v3&resultsFormat=native&siteId=744hg4&domain=https%3A%2F%2Fmarissacollections.com%2Fcollections%2F' + str(
                        collection) + '&bgfilter.collection_id=' + rid + '&bgfilter.ss_category=' + str(
                        category[0]).capitalize() + '%27s%3E' + str(category[2]).capitalize() + '&q=&page=' + str(
                        pageNo) + ''
                apiRespone = requests.get(url=apiUrl)
                apiJson = json.loads(apiRespone.content)
            except:
                pass

    def GetProducts(self, response):
        ignorProduct = self.IgnoreProduct(response)
        if ignorProduct:
            self.ProductIsOutofStock(GetterSetter.ProductUrl)
        shopify.productJson = json.loads(self.SetProductJson(response))
        categoryAndName = shopify.GetCategory(self, response) + " " + self.GetName(response)
        if (re.search(r'\b' + 'latest arrivals' + r'\b', categoryAndName, re.IGNORECASE)) and not \
                re.search(r'\b((shirt(dress?)|jump(suit?)|dress|gown|swimwear|suit|caftan)(s|es)?)\b', categoryAndName,
                          re.IGNORECASE):
            print('Skipping Non Dress Product')
            self.ProductIsOutofStock(GetterSetter.ProductUrl)
        else:
            self.GetProductInfo(response)

    # def GetName(self, response):
    #     color = self.GetSelectedColor(response)
    #     name = shopify.GetName(self, response)
    #     if not color == '' and not re.search(color, name):
    #         name = name + '-' + color
    #     return name
    #
    # def GetSelectedColor(self, response):
    #     return response.xpath(
    #         "//div[@class='swatch clearfix'][div[@class='option_title' and contains(text(),'Color')]]/div/div/text()").get().strip()

    def IgnoreProduct(self, response):
        if re.search('"availability":', response.text):
            productAvailability = response.text.split('"availability":')[1].split(',')[0].strip()
            if not 'InStock' in productAvailability:
                return True
            else:
                return False

    def GetDescription(self, response):
        baseDesc = shopify.GetDescription(self, response)
        description = response.xpath(
            "//div[@id='product-here']//div[contains(@class,'details-body')]/ul[contains(@class,'product-details-ul') or contains(@class,'product-fabrication-ul')]/li/text()").extract()
        description = ' '.join(map(str, description))
        return baseDesc + description
