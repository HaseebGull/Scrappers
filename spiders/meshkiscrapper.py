import re
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


class MeshkiScrapper(shopify):
    Spider_BaseClass.testingGender = 'women'

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(MeshkiScrapper, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        return spider

    def GetProductUrls(self, homePageResponse):
        # ========== Category And Subcategory ==========#
        topCategoryNodes = homePageResponse.xpath(
            "//ul[@class='nav']/li[a[contains(text(),'New Arrivals') or contains(text(),'Shop') or contains(text(),'Edit') or contains(text(),'Sale')]]")
        for topCategoryNode in topCategoryNodes:
            topCategoryTitle = topCategoryNode.xpath("./a/text()").get().strip()
            topCategorylink = topCategoryNode.xpath("./a/@href").get()
            if not topCategorylink.startswith(store_url):
                topCategorylink = store_url.rstrip('/') + topCategorylink

            if topCategoryTitle == "New Arrivals" or topCategoryTitle == "Sale":
                categoryNodes = topCategoryNode.xpath(
                    "./div/div[h5[contains(text(),'" + str(
                        topCategoryTitle) + "')]]/div/div//ul[contains(@class,'submenu--nested') or "
                                            "contains(@class,'submenu--single')]/li[@class='nav__item']"
                                            "/a[contains(text(),'Dresses') or contains(text(),'Jumpsuits')]")
            else:
                categoryNodes = topCategoryNode.xpath(
                    "./div/div[h5[contains(text(),'" + str(
                        topCategoryTitle) + "')]]/div/div//ul[contains(@class,'submenu--nested') or "
                                            "contains(@class,'submenu--single')][li[@class='nav__item']]")

            for categoryNode in categoryNodes:
                if topCategoryTitle == "New Arrivals" or topCategoryTitle == "Sale":
                    categoryTitle = categoryNode.xpath(
                        "./text()").get().strip()
                    categorylink = categoryNode.xpath(
                        "./@href").get()
                    if not categorylink.startswith(store_url):
                        categorylink = store_url.rstrip('/') + categorylink
                    category = 'Women ' + topCategoryTitle + " " + " " + categoryTitle
                    # ======================================#
                    self.listing(categorylink, category)
                else:
                    # =================== BREADCRUM ===================3
                    subCategoryNodes = categoryNode.xpath(
                        "./li/div[contains(text(),'DRESS') or contains(text(),'OCCASION')]/following-sibling::ul/li/a[not(contains(text(),'All'))]")
                    for subCategoryNode in subCategoryNodes:
                        subCategoryTitle = subCategoryNode.xpath("./text()").get().strip()
                        subCategorylink = subCategoryNode.xpath("./@href").get()
                        if not subCategorylink.startswith(store_url):
                            subCategorylink = store_url.rstrip('/') + subCategorylink
                        category = 'Women ' + topCategoryTitle + " " + " " + subCategoryTitle
                        # ======================================#
                        self.listing(subCategorylink, category)
        return Spider_BaseClass.AllProductUrls

    def listing(self, categorylink, category):
        collectionName = categorylink.split("/")[-1]
        categoryLinkResponse = requests.get(categorylink, stream=True)
        categoryLinkResponse = HtmlResponse(url=categorylink, body=categoryLinkResponse.text, encoding='utf-8')
        apiUrl = 'https://0eyfrdt3sh-3.algolianet.com/1/indexes/*/queries?x-algolia-agent=Algolia%20for%20JavaScript%20(4.11.0)%3B%20Browser%20(lite)%3B%20JS%20Helper%20(3.6.2)%3B%20react%20(16.8.0)%3B%20react-instantsearch%20(6.15.0)&x-algolia-api-key=14425a9ea04f90d16cfb7bc2bf73b079&x-algolia-application-id=0EYFRDT3SH'
        body = '{"requests":[{"indexName":"shopify_us_products","params":"highlightPreTag=%3Cais-highlight-0000000000%3E&highlightPostTag=%3C%2Fais-highlight-0000000000%3E&hitsPerPage=12&distinct=true&attributesToRetrieve=%5B%22handle%22%2C%22title%22%2C%22id%22%2C%22named_tags%22%2C%22sku%22%2C%22vendor%22%2C%22variants_min_price%22%2C%22variants_max_price%22%2C%22type%22%2C%22meta%22%2C%22tags%22%2C%22published_at%22%2C%22price%22%2C%22objectID%22%2C%22collections%22%2C%22product_image%22%2C%22id%22%2C%22compare_at_price%22%5D&filters=collections%3A' + str(
            collectionName) + '&maxValuesPerFacet=100&page=0&facets=%5B%22named_tags.Sub%22%2C%22named_tags.colour%22%2C%22options.size%22%2C%22named_tags.occasion%22%2C%22named_tags.fabric%22%5D&tagFilters="}]}'
        responeapi = requests.post(url=apiUrl, data=body, timeout=6000)
        apiresponse = json.loads(responeapi.content)
        totalProducts = apiresponse['results'][0]['nbHits']
        pageNo = apiresponse['results'][0]['page']
        totalPages = apiresponse['results'][0]['nbPages']
        # if totalProducts % 12 == 0:
        #     totalPages = totalProducts / 12
        # else:
        #     totalPages = totalProducts / 12 + 1
        while pageNo <= totalPages:
            pageNo += 1
            for apiproducturl in apiresponse['results'][0]['hits']:
                apiproducturl = store_url + 'products/' + apiproducturl['handle']
                productUrl = self.GetCanonicalUrl(apiproducturl)
                Spider_BaseClass.AllProductUrls.append(productUrl)
                siteMapCategory = str(Spider_BaseClass.ProductUrlsAndCategory.get(productUrl)).replace('None', '')
                if siteMapCategory:
                    Spider_BaseClass.ProductUrlsAndCategory[productUrl] = siteMapCategory + " " + ' '.join(category)
                else:
                    Spider_BaseClass.ProductUrlsAndCategory[productUrl] = ' '.join(category)
            try:
                apiUrl = 'https://0eyfrdt3sh-3.algolianet.com/1/indexes/*/queries?x-algolia-agent=Algolia%20for%20JavaScript%20(4.11.0)%3B%20Browser%20(lite)%3B%20JS%20Helper%20(3.6.2)%3B%20react%20(16.8.0)%3B%20react-instantsearch%20(6.15.0)&x-algolia-api-key=14425a9ea04f90d16cfb7bc2bf73b079&x-algolia-application-id=0EYFRDT3SH'
                body = '{"requests":[{"indexName":"shopify_us_products","params":"highlightPreTag=%3Cais-highlight-0000000000%3E&highlightPostTag=%3C%2Fais-highlight-0000000000%3E&hitsPerPage=12&distinct=true&attributesToRetrieve=%5B%22handle%22%2C%22title%22%2C%22id%22%2C%22named_tags%22%2C%22sku%22%2C%22vendor%22%2C%22variants_min_price%22%2C%22variants_max_price%22%2C%22type%22%2C%22meta%22%2C%22tags%22%2C%22published_at%22%2C%22price%22%2C%22objectID%22%2C%22collections%22%2C%22product_image%22%2C%22id%22%2C%22compare_at_price%22%5D&filters=collections%3A' + str(
                    collectionName) + '&maxValuesPerFacet=100&page=' + str(
                    pageNo) + '&facets=%5B%22named_tags.Sub%22%2C%22named_tags.colour%22%2C%22options.size%22%2C%22named_tags.occasion%22%2C%22named_tags.fabric%22%5D&tagFilters="}]}'
                responeapi = requests.post(url=apiUrl, data=body, timeout=6000)
                apiresponse = json.loads(responeapi.content)
            except:
                pass

    def IgnoreProduct(self, response):
        productAvailability = response.xpath("//meta[@property='product:availability']/@content").get()
        if re.search('InStock', productAvailability, re.IGNORECASE):
            return True
        else:
            return False
