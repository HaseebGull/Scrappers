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


class JeanjailScrapper(shopify):
    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(JeanjailScrapper, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        return spider
    # //nav[@class='theme-nav-main']/ul/li[a/span[contains(text(),'Mens') or contains(text(),'Womens')]]/div//div[contains(@class,'menu-column')][h6/a[contains(text(),'Bottoms')]]/ul/li/a[contains(text(),'Jeans')]
    def GetProductUrls(self, response):
        topCategoryNodes = response.xpath(
            "//nav[@class='theme-nav-main']/ul/li[a/span[contains(text(),'Mens') or contains(text(),'Womens')]]")
        for top_category_node in topCategoryNodes:
            top_category_title = top_category_node.xpath("./a/span/text()").get().strip()
            print("TOP CATEGORY  :", top_category_title)
            category_nodes = top_category_node.xpath(
                "./div//div[contains(@class,'menu-column')][h6/a[contains(text(),'New') or contains(text(),'Dresses') "
                "or contains(text(),'Out') or contains(text(),'Rompers')]]")
            for category_node in category_nodes:
                category_title = category_node.xpath(
                    "./h6/a/text()").get().strip()
                print("category_title :", category_title)
                sub_category_nodes = category_node.xpath("./ul/li/a[not(contains(text(),'All')) and contains(text(),"
                                                         "'Jump') or contains(text(),'suits') or contains(text(),"
                                                         "'Mi') or contains(text(),'Bridesmaids') or contains(text(),"
                                                         "'Restocked')or contains(text(),'Knits')]")
                for sub_category_node in sub_category_nodes:
                    sub_category_title = sub_category_node.xpath("./text()").get().strip()
                    sub_category_link = sub_category_node.xpath("./@href").get()
                    if not sub_category_link.startswith(store_url):
                        sub_category_link = store_url.rstrip('/') + sub_category_link
                    print(sub_category_title, " :", sub_category_link)
                    category = top_category_title + " " + category_title + " " + sub_category_title
                    self.listing(sub_category_link, category)
        return Spider_BaseClass.AllProductUrls

    def listing(self, subCategorylink, category):
        CategoryLinkResponse = requests.get(subCategorylink)
        categoryPageResponse = HtmlResponse(url=subCategorylink, body=CategoryLinkResponse.text, encoding='utf-8')
        global rid
        if re.search('"rid":', CategoryLinkResponse.text):
            rid = CategoryLinkResponse.text.split('"rid":')[1].split('}')[0]
        collectionName = subCategorylink.split("/")[-1]
        api_url = 'https://www.searchanise.com/getresults?api_key=1e7E8x5K1y&q=&sortBy=collection_' + str(
            rid) + '_position&sortOrder=asc&startIndex=40&maxResults=40&items=true&pages=true&categories=true&suggestions=true&queryCorrection=true&suggestionsMaxResults=3&pageStartIndex=0&pagesMaxResults=0&categoryStartIndex=0&categoriesMaxResults=0&facets=true&facetsShowUnavailableOptions=false&ResultsTitleStrings=2&ResultsDescriptionStrings=0&tab=products&page=1&collection=' + str(
            collectionName) + '&output=jsonp'
        responeapi = requests.get(url=api_url, timeout=6000)
        apiresponse = json.loads(responeapi.content)
        page_no = 2
        totalItems = apiresponse['totalItems']
        itemsPerPage = apiresponse['itemsPerPage']
        if totalItems % itemsPerPage == 0:
            totalPages = totalItems / itemsPerPage
        else:
            totalPages = totalItems / itemsPerPage + 1
        totalPages = str(totalPages).split('.')[0]
        print("TOTALPAGE :", totalPages)
        while page_no <= int(totalPages):
            page_no += 1
            product_list = apiresponse['items']
            for product_url in product_list:
                product_url = product_url['link']
                if not product_url.startswith(store_url):
                    product_url = store_url.rstrip('/') + product_url
                print("Product-Url :", product_url)
                product_url = self.GetCanonicalUrl(product_url)
                Spider_BaseClass.AllProductUrls.append(product_url)
                siteMapCategory = str(Spider_BaseClass.ProductUrlsAndCategory.get(product_url)).replace('None', '')
                if siteMapCategory:
                    Spider_BaseClass.ProductUrlsAndCategory[product_url] = siteMapCategory + " " + category
                else:
                    Spider_BaseClass.ProductUrlsAndCategory[product_url] = category
            try:
                api_url = 'https://www.searchanise.com/getresults?api_key=1e7E8x5K1y&q=&sortBy=collection_' + str(
                    rid) + '_position&sortOrder=asc&startIndex=40&maxResults=40&items=true&pages=true&categories=true&suggestions=true&queryCorrection=true&suggestionsMaxResults=3&pageStartIndex=0&pagesMaxResults=0&categoryStartIndex=0&categoriesMaxResults=0&facets=true&facetsShowUnavailableOptions=false&ResultsTitleStrings=2&ResultsDescriptionStrings=0&tab=products&page=' + str(
                    page_no) + '&collection=' + str(collectionName) + '&output=jsonp'
                responeapi = requests.get(url=api_url, timeout=6000)
                apiresponse = json.loads(responeapi.content)
            except:
                pass

    def GetProducts(self, response):
        ignorProduct = self.IgnoreProduct(response)
        if ignorProduct == True:
            self.ProductIsOutofStock(GetterSetter.ProductUrl)
        shopify.productJson = json.loads(self.SetProductJson(response))
        categoryAndName = shopify.GetCategory(self, response) + " " + self.GetName(response)
        if (re.search(r'\b' + 'new' + r'\b', categoryAndName, re.IGNORECASE)) and not \
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
