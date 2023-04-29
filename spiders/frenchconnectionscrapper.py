import re
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


class FrenchconnectionScrapper(shopify):
    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(FrenchconnectionScrapper, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        return spider

    def GetProductUrls(self, response):
        topCategoryNodes = response.xpath(
            "(//nav[@id='site-navigation']/ul/li[a[contains(text(),'Woman') or contains(text(),'Man') or contains(text(),'Sale')]])[1]")
        for top_category_node in topCategoryNodes:
            top_category_title = top_category_node.xpath("./a/text()").get().strip()
            print("TOP CATEGORY  :", top_category_title)
            category_nodes = top_category_node.xpath(
                "(./div/ul/li[a[contains(text(),'Clothing') or contains(text(),'Edit') or contains(text(),'Sale')]])[1]")
            for category_node in category_nodes:
                category_title = category_node.xpath("./a/text()").get().strip()
                print("category_title :", category_title)
                sub_category_nodes = category_node.xpath(
                    "(./ul/li/a[contains(text(),'Dresses') or contains(text(),'Jumpsuits') or contains(text(),'Loungewear')])[1]")
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
            rid = categoryPageResponse.text.split('"rid":')[1].split('}')[0]
        api_url = 'https://services.mybcapps.com/bc-sf-filter/filter?t=1659429263599&_=pf&shop=frenchconnectionus' \
                  '.myshopify.com&page=1&limit=40&sort=manual&display=grid&collection_scope=' + str(rid) + '&tag=&product_available=false'
        responeapi = requests.get(url=api_url, timeout=6000)
        apiresponse = json.loads(responeapi.content)
        total_products = apiresponse['total_product']
        itemsPerPage = 40
        page_no = 1
        if total_products % itemsPerPage == 0:
            totalPages = total_products / itemsPerPage
        else:
            totalPages = total_products / itemsPerPage + 1
        totalPages = str(totalPages).split('.')[0]
        print("TOTALPAGE :", totalPages)
        while page_no <= int(totalPages):
            page_no += 1
            product_list = apiresponse['products']
            for product_url in product_list:
                product_url = product_url['handle']
                if not product_url.startswith(store_url):
                    product_url = store_url + 'products/' + product_url
                print("Product-Url :", product_url)
                product_url = self.GetCanonicalUrl(product_url)
                Spider_BaseClass.AllProductUrls.append(product_url)
                siteMapCategory = str(Spider_BaseClass.ProductUrlsAndCategory.get(product_url)).replace('None', '')
                if siteMapCategory:
                    Spider_BaseClass.ProductUrlsAndCategory[product_url] = siteMapCategory + " " + category
                else:
                    Spider_BaseClass.ProductUrlsAndCategory[product_url] = category
            try:
                api_url = 'https://services.mybcapps.com/bc-sf-filter/filter?t=1659429263599&_=pf&shop=frenchconnectionus.myshopify.com&page=' + str(page_no) + '&limit=40&sort=manual&display=grid&collection_scope=' + str(rid) + '&tag=&product_available=false'
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
