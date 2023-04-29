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


class Motherdenimscrapper(shopify):

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(Motherdenimscrapper, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        return spider

    def GetProductUrls(self, homePageResponse):
        # ========== Category And Subcategory ==========#
        topCategoryNodes = homePageResponse.xpath(
            "//ul[contains(@class,'tems-center')]/li[contains(@id,'women') or contains(@id,'men')]/div/a/span/text()")
        for topCategoryNode in topCategoryNodes:
            topCategoryTitle = topCategoryNode.xpath("./a/span/text()").get().strip()
            topCategorylink = topCategoryNode.xpath("./a/@href").get().strip()
            if not topCategorylink.startswith(store_url):
                topCategorylink = store_url.rstrip('/') + topCategorylink
            print("TOP CATEGORY  :", topCategoryTitle, ",TOP CATEGORY LINK  :", topCategorylink)

            categoryNodes = topCategoryNode.xpath(
                "./following-sibling::div/div//ul/li/a[contains(text(),'Clothing')]/following-sibling::ul/li/a[contains(text(),'Dress') or contains(text(),'Jumpsuits')]")
            print(categoryNodes)
            for categoryNode in categoryNodes:
                categoryTitle = categoryNode.xpath("./text()").get().strip()
                categorylink = categoryNode.xpath("./@href").get()
                if not categorylink.startswith(store_url):
                    categorylink = store_url.rstrip('/') + categorylink
                if re.search('\?', categorylink):
                    categorylink = 'https' + categorylink.split('https' or 'http')[1].split('?')[0].strip()
                print("CATEGORY  :", categoryTitle)

                subCategoryNodes = homePageResponse.xpath(
                    "./following-sibling::ul/li/a[contains(text(),'Dress') or contains(text(),'Jumpsuits')]")
                for subCategoryNode in subCategoryNodes:
                    subCategoryTitle = subCategoryNode.xpath("./text()").get().strip()
                    if 'BRANDS' in topCategoryTitle:
                        subCategoryTitle = 'Women' + subCategoryTitle
                    subCategorylink = subCategoryNode.xpath("./@href").get()
                    if not subCategorylink.startswith(store_url):
                        subCategorylink = store_url.rstrip('/') + subCategorylink
                    if re.search('\?', subCategorylink):
                        subCategorylink = 'https' + subCategorylink.split('https' or 'http')[1].split('?')[0].strip()
                    print("CATEGORY  :", categoryTitle)
                    category = topCategoryTitle + " " + categoryTitle + " " + subCategoryTitle
                    # self.listing(categorylink, category)
        return Spider_BaseClass.AllProductUrls

    def listing(self, categorylink, category):
        categoryLinkResponse = requests.get(categorylink)
        categoryLinkResponse = HtmlResponse(url=categorylink, body=categoryLinkResponse.text, encoding='utf-8')
        if re.search('collection="', categoryLinkResponse.text):
            collection_id = categoryLinkResponse.text.split(' collection="')[1].split('"')[0]
            Dresses = categoryLinkResponse.text.split(' collection-name="')[1].split('"')[0]
            apiUrl = 'https://00svms.a.searchspring.io/api/search/search.json?ajaxCatalog=v3&resultsFormat=native&siteId=00svms&domain=' + categorylink + '&bgfilter.is_published=yes&bgfilter.collection_name=' + Dresses + '&bgfilter.ss_mother_hide=0&bgfilter.collection_id=' + collection_id + '&q=&page=1'
            apiresponse = requests.post(url=apiUrl, timeout=6000)
            apiresponseJson = json.loads(apiresponse.content)
            totalPage = apiresponseJson['pagination']['totalPages']
            pageNo = 2
            self.GetUrls(apiresponseJson, category)
            while pageNo <= totalPage:
                nextPageUrl = 'https://00svms.a.searchspring.io/api/search/search.json?ajaxCatalog=v3&resultsFormat=native&siteId=00svms&domain=' + categorylink + '&bgfilter.is_published=yes&bgfilter.collection_name=' + Dresses + '&bgfilter.ss_mother_hide=0&bgfilter.collection_id=' + collection_id + '&q=&page=' + str(
                    pageNo)
                apiresponse = requests.get(url=nextPageUrl, timeout=6000)
                apiresponseJson = json.loads(apiresponse.content)
                self.GetUrls(apiresponseJson, category)
                pageNo = pageNo + 1

    def GetUrls(self, datJson, category):
        for proNode in datJson['results']:
            productUrl = proNode['url']
            if not productUrl.startswith(store_url):
                productUrl = store_url.rstrip('/') + productUrl
            print('PRODUCT URL : ', productUrl)
            Spider_BaseClass.AllProductUrls.append(productUrl)
            siteMapCategory = str(Spider_BaseClass.ProductUrlsAndCategory.get(productUrl)).replace('None', '')
            if siteMapCategory:
                Spider_BaseClass.ProductUrlsAndCategory[productUrl] = siteMapCategory + " " + category
            else:
                Spider_BaseClass.ProductUrlsAndCategory[productUrl] = category

    def SetproductJson(self, response):
        if re.search('productJson={', response.text):
            ProductJsonStr = '{' + response.text.split('productJson={')[1].split('"content"')[
                0].strip().rstrip(',') + '}'
        elif re.search('rv.products.unshift\({', response.text):
            ProductJsonStr = '{' + response.text.split('rv.products.unshift({')[1].split('"content"')[0].strip().rstrip(
                ',') + '}'
        else:
            print("Invoke product json api for: ", GetterSetter.ProductUrl)
            ProductJsonStr = requests.get(GetterSetter.ProductUrl + '.js', cookies=shopify.cookies_dict).content
        return ProductJsonStr

    def GetName(self, response):
        return shopify.productJson["title"]
