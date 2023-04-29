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


class AllsaintsScrapper(Spider_BaseClass):
    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(AllsaintsScrapper, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        return spider

    def GetProductUrls(self, homePageResponse):
        # ========== Category And Subcategory ==========#
        topCategoryNodes = homePageResponse.xpath(
            "//div[contains(@class,'header__row')]/div/nav/ul/li[a[contains(text(),'WOMEN')]]")
        for topCategoryNode in topCategoryNodes:
            topCategoryNodeTitle = topCategoryNode.xpath("./a/text()").get().strip()
            topCategoryNodelink = topCategoryNode.xpath("./a/@href").get()
            if not topCategoryNodelink.startswith(store_url):
                topCategoryNodelink = store_url.rstrip('/') + topCategoryNodelink
            print("TOP CATEGORY TITLE :", topCategoryNodeTitle)
            print("TOP CATEGORY LINK  :", topCategoryNodelink)
            categoryNodes = topCategoryNode.xpath(
                "./div//div[@class='row']/div/div[a[contains(text(),'SHOP') or contains(text(),'CLOTHING')]]")
            for categoryNode in categoryNodes:
                categoryNodeTitle = categoryNode.xpath("./a/text()").get().strip()
                categoryNodelink = categoryNode.xpath("./a/@href").get()
                if not categoryNodelink.startswith(store_url):
                    categoryNodelink = store_url.rstrip('/') + categoryNodelink
                print("CATEGORY TITLE :", categoryNodeTitle)
                print("CATEGORY LINK  :", categoryNodelink)
                subCategoryNodes = categoryNode.xpath(
                    "./ul/li/a[contains(text(),'Sale') or contains(text(),'New Arrivals') or contains(text(),'Dresses')]")
                for subCategoryNode in subCategoryNodes:
                    subCategoryNodeTitle = subCategoryNode.xpath("./text()").get().strip()
                    subCategoryNodelink = subCategoryNode.xpath("./@href").get()
                    if not subCategoryNodelink.startswith(store_url):
                        subCategoryNodelink = store_url.rstrip('/') + subCategoryNodelink
                    print("SUB CATEGORY TITLE :", subCategoryNodeTitle)
                    print("SUB CATEGORY LINK  :", subCategoryNodelink)
                    category = topCategoryNodeTitle + " " + categoryNodeTitle + " " + subCategoryNodeTitle
                    self.listing(subCategoryNodelink, category)
        return Spider_BaseClass.AllProductUrls

    def listing(self, subCategoryNodelink, category):
        subCategoryLinkResponse = requests.get(subCategoryNodelink)
        subCategoryLinkResponse = HtmlResponse(url=subCategoryNodelink, body=subCategoryLinkResponse.text,
                                               encoding='utf-8', )
        filterNodes = subCategoryLinkResponse.xpath(
            "//div[contains(@class,'category-page-filters') and contains(text(),'FILTER')]/following-sibling::button[@data-filter!='colour' and @data-filter!='size' and @data-filter!='price_range' and @data-filter!='sorting']")
        for filterNode in filterNodes:
            filterTag = filterNode.xpath("./div/span/text()").get()
            filterType = filterNode.xpath("./@data-filter").get()
            if filterType == 'style':
                filters = filterNode.xpath(
                    "./following-sibling::div[@data-filter='" + filterType + "']/div/div/input[not(@disabled)]")
                for filter in filters:
                    filterName = filter.xpath("./@name").get()
                    firstFilterValue = filter.xpath("./@value").get()
                    print('FILTER NAME AND VALUE ', filterName, firstFilterValue)
                    url = subCategoryNodelink + 'style,' + firstFilterValue + '/colour,any/size,any/'
                    filtersResponse = requests.get(url)
                    filtersResponse = HtmlResponse(url=url, body=filtersResponse.text, encoding='utf-8', )
                    filterNodes = filtersResponse.xpath(
                        "//div[contains(@class,'category-page-filters') and contains(text(),'FILTER')]/following-sibling::button[@data-filter!='colour' and @data-filter!='size' and @data-filter!='price_range' and @data-filter!='sorting']")
                    for filterNode in filterNodes:

                        filterType = filterNode.xpath("./@data-filter").get()
                        if filterType == 'fabric':
                            filters = filterNode.xpath(
                                "./following-sibling::div[@data-filter='" + filterType + "']/div/div/input[not(@disabled)]")
                            for filter in filters:
                                filterName = filter.xpath("./@name").get()
                                secondFilterValue = filter.xpath("./@value").get()
                                url = subCategoryNodelink + 'style,' + firstFilterValue + '/colour,any/size,any/fabric,' + secondFilterValue + '/'
                                filtersResponse = requests.get(url)
                                filtersResponse = HtmlResponse(url=url, body=filtersResponse.text, encoding='utf-8', )
                                filterNodes = filtersResponse.xpath(
                                    "//div[contains(@class,'category-page-filters') and contains(text(),'FILTER')]/following-sibling::button[@data-filter!='colour' and @data-filter!='size' and @data-filter!='price_range' and @data-filter!='sorting']")
                                for filterNode in filterNodes:
                                    filterType = filterNode.xpath("./@data-filter").get()
                                    if filterType == 'length':
                                        filters = filterNode.xpath(
                                            "./following-sibling::div[@data-filter='" + filterType + "']/div/div/input[not(@disabled)]")
                                        for filter in filters:
                                            filterName = filter.xpath("./@name").get()
                                            thirdFilterValue = filter.xpath("./@value").get()
                                            url = subCategoryNodelink + 'style,' + firstFilterValue + '/colour,any/size,any/fabric,' + secondFilterValue + '/length,' + thirdFilterValue + '/'
                                            filtersResponse = requests.get(url)
                                            filtersResponse = HtmlResponse(url=url, body=filtersResponse.text,
                                                                           encoding='utf-8', )
                                            product_list = filtersResponse.xpath(
                                                "//a[@class='mainImg']/@href").extract()
                                            for productUrl in product_list:
                                                if not productUrl.startswith(store_url):
                                                    productUrl = store_url.rstrip('/') + productUrl
                                                print('Product Url: ', productUrl)
                                                Spider_BaseClass.AllProductUrls.append(productUrl)
                                                try:
                                                    filterCategory = Spider_BaseClass.ProductUrlsAndCategory[productUrl]
                                                    if filterCategory:
                                                        filterCategory = filterCategory + " " + category
                                                        Spider_BaseClass.ProductUrlsAndCategory[
                                                            productUrl] = filterCategory
                                                except:
                                                    Spider_BaseClass.ProductUrlsAndCategory[productUrl] = category


