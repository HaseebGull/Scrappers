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


class Bebescrapper(shopify):
    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(Bebescrapper, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        return spider

    def GetProductUrls(self, homePageResponse):
        # ========== Category And Subcategory ==========#
        topCategoryNodes = homePageResponse.xpath(
            "//nav[@id='nav']/div/ul/li[a[contains(text(),'Clothing') or contains(text(),'Dresses') or contains(text(),'Sale') or contains(text(),'New')]]")
        for topCategoryNode in topCategoryNodes:
            topCategoryTitle = topCategoryNode.xpath("./a/text()").get().strip()
            if not 'Women' in topCategoryTitle:
                topCategoryTitle = 'Women' + " " + topCategoryTitle
            topCategorylink = topCategoryNode.xpath("./a/@href").get()
            if not topCategorylink.startswith(store_url):
                topCategorylink = store_url.rstrip('/') + topCategorylink
            categoryNodes = topCategoryNode.xpath(
                ".//ul/div/span/li/h5/a[not(contains(text(),'All')) and (contains(text(),'Dress')) or contains(text(),'Sale') or contains(text(),'Jumpsuits') or contains(text(),'New') or contains(text(),'Sleep')]")
            for categoryNode in categoryNodes:
                categoryTitle = categoryNode.xpath("./text()").get().strip()
                categorylink = categoryNode.xpath("./@href").get()
                if not categorylink.startswith(store_url):
                    categorylink = store_url.rstrip('/') + categorylink
                if 'Clothing' in topCategoryTitle and categoryTitle == 'Sale' \
                        or 'Sale' in topCategoryTitle and categoryTitle == 'All Sale' \
                        or 'Sale' in topCategoryTitle and categoryTitle == 'Final Sale':
                    continue
                else:
                    category = topCategoryTitle + " " + categoryTitle
                    self.listing(categorylink, category)
        return Spider_BaseClass.AllProductUrls

    def listing(self, categorylink, category):
        CategoryLinkResponse = requests.get(categorylink)
        CategoryLinkResponse = HtmlResponse(url=categorylink, body=CategoryLinkResponse.text, encoding='utf-8')

        global rid
        if re.search('"rid":', CategoryLinkResponse.text):
            rid = CategoryLinkResponse.text.split('"rid":')[1].split('}')[0]
        apiUrl = 'https://services.mybcapps.com/bc-sf-filter/filter?t=1640081497018&page=1&shop=bebe-prod.myshopify' \
                 '.com&limit=40&sort=manual&display=grid&collection_scope=' + str(
            rid) + '&product_available=true&variant_available=true&build_filter_tree=true&check_cache=false'
        responeapi = requests.get(url=apiUrl, timeout=6000)
        apiresponse = json.loads(responeapi.content)
        totalProducts = apiresponse['total_product']
        totalPages = 0
        pageNo = 1
        if totalProducts % 40 == 0:
            totalPages = totalProducts / 40
        else:
            totalPages = totalProducts / 40 + 1
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
                apiUrl = 'https://services.mybcapps.com/bc-sf-filter/filter?t=1640081497018&page=' + str(
                    pageNo) + '&shop=bebe-prod.myshopify.com&limit=40&sort=manual&display=grid&collection_scope=' + str(
                    rid) + '&product_available=true&variant_available=true&build_filter_tree=true&check_cache=false'
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
        if (re.search('sale', categoryAndName, re.IGNORECASE) or re.search('New', categoryAndName,
                                                                           re.IGNORECASE) or re.search('new arrival',
                                                                                                       categoryAndName,
                                                                                                       re.IGNORECASE)) and not re.search(
            r'\b((shirt(dress?)|jump(suit?)|dress|gown|suit|caftan)(s|es)?)\b', categoryAndName, re.IGNORECASE):
            print('Skipping Non Dress Product')
            self.ProductIsOutofStock(GetterSetter.ProductUrl)
        else:
            self.GetProductInfo(response)

    def GetName(self, response):
        color = self.GetSelectedColor(response)
        name = shopify.GetName(self, response)
        if not color == '' and not re.search(color, name):
            name = name + ' - ' + color
        return name

    def GetSelectedColor(self, response):
        return response.xpath("//div[@class='swatch-header']/h6[@class='current-option']/text()").get().strip()

    def IgnoreProduct(self, response):
        if re.search('"availability":', response.text):
            productAvailability = response.text.split('"availability":')[1].split(',')[0].strip()
            if not 'InStock' in productAvailability:
                return True
            else:
                return False
