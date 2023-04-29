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


class LordandTaylorScrapper(shopify):
    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(LordandTaylorScrapper, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        return spider

    def GetProductUrls(self, homePageResponse):
        # ========== Category And Subcategory ==========#
        genderNodes = homePageResponse.xpath(
            "//div[contains(@class,'eader-item--left')]/ul/li[contains(@main-section,'women') or contains(@main-section,'men')]/a")
        for genderNode in genderNodes:
            genderTitle = genderNode.xpath("./text()").get().strip()
            genderlink = genderNode.xpath("./@href").get()
            if not genderlink.startswith(store_url):
                genderlink = store_url.rstrip('/') + genderlink

            topCategoryNodes = homePageResponse.xpath(
                "//ul[@section-name='" + genderTitle.lower() + "']/li[a[contains(text(),'CLOTHING') or contains(text(),'SALE')]]")
            for topCategoryNode in topCategoryNodes:
                topCategoryTitle = topCategoryNode.xpath("./a/text()").get().strip()
                topCategorylink = topCategoryNode.xpath("./a/@href").get()
                if not topCategorylink.startswith(store_url):
                    topCategorylink = store_url.rstrip('/') + topCategorylink

                categoryNodes = topCategoryNode.xpath(
                    "./div//div[@class='h5'][a[contains(text(),'Clothing') or contains(text(),'Plus') or contains(text(),'Womens Sale') or contains(text(),'Mens Sale')]]")
                for categoryNode in categoryNodes:
                    categoryTitle = categoryNode.xpath("./a/text()").get().strip()
                    categorylink = categoryNode.xpath("./a/@href").get()
                    if not categorylink.startswith(store_url):
                        categorylink = store_url.rstrip('/') + categorylink
                    subCategoryNodes = categoryNode.xpath(
                        "./following-sibling::div/a[contains(text(),'Jumpsuits') or contains(text(),'New') or contains(text(),'Dress') or contains(text(),'Suiting')]")
                    for subCategoryNode in subCategoryNodes:
                        subCategoryTitle = subCategoryNode.xpath("./text()").get().strip()
                        subCategorylink = subCategoryNode.xpath("./@href").get()
                        if not subCategorylink.startswith(store_url):
                            subCategorylink = store_url.rstrip('/') + subCategorylink
                        # =================== BREADCRUM ===================3
                        category = genderTitle + " " + topCategoryTitle + " " + categoryTitle + " " + subCategoryTitle
                        # ======================================#
                        self.listing(subCategorylink, category)
        return Spider_BaseClass.AllProductUrls

    def listing(self, categorylink, category):
        CategoryLinkResponse = requests.get(categorylink)
        categoryPageResponse = HtmlResponse(url=categorylink, body=CategoryLinkResponse.text, encoding='utf-8')
        global collectionName
        if re.search('"collectionName":"', CategoryLinkResponse.text):
            collectionName = CategoryLinkResponse.text.split('"collectionName":"')[1].split('",')[0]

        global rid
        if re.search('"rid":', CategoryLinkResponse.text):
            rid = CategoryLinkResponse.text.split('"rid":')[1].split('}')[0]

        apiUrl = 'https://ultimate-dot-acp-magento.appspot.com/categories_navigation?q=&page_num=1&store_id=51614548144&UUID=5da1aba8-0aef-40af-9edd-ddbd29b0eb13&cdn_cache_key=1646982669&sort_by=relevency&facets_required=0&callback=ispSearchResult&related_search=1&with_product_attributes=1&category_id=' + str(
            rid) + '&category_url=%2Fcollections%2F' + collectionName + ''
        responeapi = requests.get(url=apiUrl, timeout=6000)
        if re.search("ispSearchResult\(", responeapi.text):
            responeapi = responeapi.text.split("ispSearchResult(")[1].split('"});')[0] + '"}'
        apiresponse = json.loads(responeapi)
        totalProducts = apiresponse['total_results']
        pageNo = apiresponse['p']
        totalPages = apiresponse['total_p']
        self.GetUrls(apiresponse, category)
        while pageNo != totalPages:
            pageNo = pageNo + 1
            nextPageApiUrl = 'https://ultimate-dot-acp-magento.appspot.com/categories_navigation?q=&page_num=' + str(
                pageNo) + '&store_id=51614548144&UUID=5da1aba8-0aef-40af-9edd-ddbd29b0eb13&cdn_cache_key=1646982669&sort_by=relevency&facets_required=0&callback=ispSearchResult&related_search=1&with_product_attributes=1&category_id=' + str(
                rid) + '&category_url=%2Fcollections%2F' + collectionName + ''
            responeapi = requests.get(url=nextPageApiUrl, timeout=6000)
            if re.search("ispSearchResult\(", responeapi.text):
                responeapi = responeapi.text.split("ispSearchResult(")[1].split('"});')[0] + '"}'
            apiresponse = json.loads(responeapi)
            self.GetUrls(apiresponse, category)

    def GetUrls(self, dataJson, category):
        for apiproduct in dataJson['items']:
            apiproducturl = apiproduct['u']
            if not apiproducturl.startswith(store_url):
                apiproducturl = store_url.rstrip('/') + apiproduct['u']
            productUrl = self.GetCanonicalUrl(apiproducturl)
            Spider_BaseClass.AllProductUrls.append(productUrl)
            siteMapCategory = str(Spider_BaseClass.ProductUrlsAndCategory.get(productUrl)).replace('None', '')
            if siteMapCategory:
                Spider_BaseClass.ProductUrlsAndCategory[productUrl] = siteMapCategory + " " + category
            else:
                Spider_BaseClass.ProductUrlsAndCategory[productUrl] = category

    def GetProducts(self, response):
        ignorProduct = self.IgnoreProduct(response)
        if ignorProduct == True:
            self.ProductIsOutofStock(GetterSetter.ProductUrl)
        shopify.productJson = json.loads(self.SetProductJson(response))
        categoryAndName = shopify.GetCategory(self, response) + " " + self.GetName(response)
        if (re.search('New Arrivals', categoryAndName, re.IGNORECASE)) and not \
                re.search(r'\b((shirt(dress?)|jump(suit?)|dress|set|Romper|gown|suit|caftan)(s|es)?)\b',
                          categoryAndName,
                          re.IGNORECASE):
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
        return response.xpath(
            "//span[contains(@class,'option_name') and contains(text(),'Color')]/following-sibling::span/span/text()").get().strip()

    def IgnoreProduct(self, response):
        if re.search('"availability":', response.text):
            productAvailability = response.text.split('"availability":')[1].split(',')[0].strip()
            if not 'InStock' in productAvailability:
                return True
            else:
                return False
