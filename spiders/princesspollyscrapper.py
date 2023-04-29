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


class PrincessPollyScrapper(shopify):
    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(PrincessPollyScrapper, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        return spider

    def GetProductUrls(self, homePageResponse):
        # ========== Category And Subcategory ==========#
        topCategoryNodes = homePageResponse.xpath(
            "//nav[@class='nav']/div/div[a[contains(span/span/text(),'Clothing') or contains(span/span/text(),'New') "
            "or contains(span/span/text(),'Dress') or contains(span/span/text(),'Sale')]]")
        for topCategoryNode in topCategoryNodes:
            topCategoryTitle = topCategoryNode.xpath("./a/span/span/text()").get().strip()
            topCategorylink = topCategoryNode.xpath("./a/@href").get()
            if not topCategorylink.startswith(store_url):
                topCategorylink = store_url.rstrip('/') + topCategorylink
            categoryNodes = topCategoryNode.xpath(
                "./div/div/div/div[a[contains(text(),'Just In') or contains(text(),'Dress') or contains(text(),'Romper') "
                "or contains(text(),'Curve') or contains(text(),'Style') or contains(text(),'Occasion') "
                "or contains(text(),'Color') or contains(text(),'Tops') or text()='Sale']]")
            for categoryNode in categoryNodes:
                categoryTitle = categoryNode.xpath("./a/text()").get().strip()
                categorylink = categoryNode.xpath("./a/@href").get()
                if not categorylink.startswith(store_url):
                    categorylink = store_url.rstrip('/') + categorylink
                if re.search('\?', categorylink):
                    categorylink = 'https' + categorylink.split('https' or 'http')[1].split('?')[0].strip()
                # =================== BREADCRUM ===================3
                subCategoryNodes = categoryNode.xpath(
                    "./div/div/a[not(contains(text(),'All')) and contains(text(),'Dress') or contains(text(),'Romper') "
                    "or contains(text(),'Jumpsuit') or contains(text(),'Bodysuit')]")
                for subCategoryNode in subCategoryNodes:
                    subCategoryTitle = subCategoryNode.xpath("./text()").get().strip()
                    subCategorylink = subCategoryNode.xpath("./@href").get()
                    if not subCategorylink.startswith(store_url):
                        subCategorylink = store_url.rstrip('/') + subCategorylink
                    category = 'Women ' + topCategoryTitle + " " + categoryTitle + " " + subCategoryTitle
                    # ======================================#
                    self.listing(subCategorylink, category)
        return Spider_BaseClass.AllProductUrls

    def listing(self, categorylink, category):
        CategoryLinkResponse = requests.get(categorylink)
        CategoryLinkResponse = HtmlResponse(url=categorylink, body=CategoryLinkResponse.text, encoding='utf-8')
        global rid
        if re.search('"rid":', CategoryLinkResponse.text):
            rid = CategoryLinkResponse.text.split('"rid":')[1].split('}')[0]
        apiUrl = 'https://services.mybcapps.com/bc-sf-filter/filter?shop=princesspollydev.myshopify.com&page=1&currency=usd&limit=60&sort=manual&display=grid&collection_scope=' + str(
            rid) + '&product_available=true&variant_available=true&build_filter_tree=true&check_cache=true'
        responeapi = requests.get(url=apiUrl, timeout=6000)
        apiresponse = json.loads(responeapi.content)
        totalProducts = apiresponse['total_product']
        totalPages = 0
        pageNo = 1
        if totalProducts % 60 == 0:
            totalPages = totalProducts / 60
        else:
            totalPages = totalProducts / 60 + 1
        print(totalPages)
        while pageNo <= totalPages:
            pageNo += 1
            for apiproducturl in apiresponse['products']:
                apiproducturl = store_url + 'products/' + apiproducturl['handle']
                productUrl = self.GetCanonicalUrl(apiproducturl)
                Spider_BaseClass.AllProductUrls.append(productUrl)
                siteMapCategory = str(Spider_BaseClass.ProductUrlsAndCategory.get(productUrl)).replace('None', '')
                if siteMapCategory:
                    Spider_BaseClass.ProductUrlsAndCategory[productUrl] = siteMapCategory + " " + category
                else:
                    Spider_BaseClass.ProductUrlsAndCategory[productUrl] = category
            try:
                apiUrl = 'https://services.mybcapps.com/bc-sf-filter/filter?shop=princesspollydev.myshopify.com&page=' + str(
                    pageNo) + '&currency=usd&limit=60&sort=manual&display=grid&collection_scope=' + str(
                    rid) + '&product_available=true&variant_available=true&build_filter_tree=true&check_cache=true'
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
        if (re.search('New Rompers & Sets', categoryAndName, re.IGNORECASE)) and not \
                re.search(r'\b((shirt(dress?)|jump(suit?)|dress|set|romper|gown|suit|caftan)(s|es)?)\b',
                          categoryAndName,
                          re.IGNORECASE):
            print('Skipping Non Dress Product')
            self.ProductIsOutofStock(GetterSetter.ProductUrl)
        else:
            self.GetProductInfo(response)

    def IgnoreProduct(self, response):
        productAvailability = response.xpath("//link[@itemprop='availability']/@href").get()
        if not 'InStock' in productAvailability:
            return True
        else:
            return False
