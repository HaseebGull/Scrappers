import sys
from pathlib import Path

from seleniumfile import SeleniumResponse

DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(DIR.parent.parent.parent.parent))
__package__ = DIR.name

import django

django.setup()
from BaseClass import *
from scrapy import signals

store_url = sys.argv[4]


class SelfridgesScrapper(Spider_BaseClass):
    Spider_BaseClass.cookies_dict = {"currency": "USD", "currencyOverride": "USD"}

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(SelfridgesScrapper, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        return spider

    def GetProductUrls(self, homePageResponse):
        # ========== Category And Subcategory ==========#
        if not homePageResponse:
            print('aa')
            homePageResponse = SeleniumResponse(store_url)

        topCategoryNodes = homePageResponse.xpath(
            "//ul[contains(@class,'megamenu-category')]/li/a[contains(@data-analytics-label,'Women')]")
        for topCategoryNode in topCategoryNodes:
            type = topCategoryNode.xpath("./@data-analytics-type)").get().strip()
            topCategoryTitle = topCategoryNode.xpath("./text()").get().strip()
            topCategorylink = topCategoryNode.xpath("./@href").get()
            if not topCategorylink.startswith(store_url):
                topCategorylink = store_url.rstrip('/') + topCategorylink
            print("TOP CATEGORY  :", topCategoryTitle, "TOP CATEGORY LINK  :", topCategorylink)
            categoryNodes = topCategoryNode.xpath(
                "//div[contains(@class,'ccwomen') and contains(@data-analytics-type,'" + type + "')]/div//dl[dt/h3/a[contains(text(),'All clothing')]]")
            for categoryNode in categoryNodes:
                categoryTitle = categoryNode.xpath("./text()").get().strip()
                categorylink = categoryNode.xpath("./@href").get()
                if not categorylink.startswith(store_url):
                    categorylink = store_url.rstrip('/') + categorylink
                print("CATEGORY  :", categoryTitle, "CATEGORY LINK  :", categorylink)

                subCategoryNodes = categoryNode.xpath(
                    "./dd/a[contains(text(),'Dress') or contains(text(),'Jumpsuits') or contains(text(),'dress')]")
                for subCategoryNode in subCategoryNodes:
                    subCategoryTitle = subCategoryNode.xpath("./text()").get().strip()
                    subCategorylink = subCategoryNode.xpath("./@href").get()
                    if not subCategorylink.startswith(store_url):
                        subCategorylink = store_url.rstrip('/') + subCategorylink
                    print("SUB CATEGORY  :", subCategoryTitle, "SUB CATEGORY LINK  :", subCategorylink)
                    category = topCategoryTitle + " " + categoryTitle + " " + subCategoryTitle
                    print("BreadCrum : ", category)
                    self.listing(subCategorylink, category)

        return Spider_BaseClass.AllProductUrls

    def listing(self, categorylink, category):
        categoryLinkResponse = requests.get(categorylink, stream=True)
        categoryLinkResponse = HtmlResponse(url=categorylink, body=categoryLinkResponse.text, encoding='utf-8')
        product_list = categoryLinkResponse.xpath(
            "//a[contains(@class,'product-link')]/@href").extract()
        for productUrl in product_list:
            if not productUrl.startswith(store_url):
                productUrl = store_url.rstrip('/') + productUrl
            if re.search('https://', productUrl) and re.search('\?', productUrl):
                productUrl = 'https://' + productUrl.split('https://')[1].split('?')[0].strip()
            print("Product URL  :", productUrl)
            Spider_BaseClass.AllProductUrls.append(productUrl)
            siteMapCategory = str(Spider_BaseClass.ProductUrlsAndCategory.get(productUrl)).replace('None', '')
            if siteMapCategory:
                Spider_BaseClass.ProductUrlsAndCategory[productUrl] = siteMapCategory + " " + category
            else:
                Spider_BaseClass.ProductUrlsAndCategory[productUrl] = category
        try:
            nextPageUrl = categoryLinkResponse.xpath(
                "//a[@rel='next' and contains(@href, 'javascript:setPageNumber') and not(contains(@href, 'javascript:void(0);'))]/@href").get()
            print('nextPageUrl:', nextPageUrl)
            self.listing(nextPageUrl, category)
        except:
            print('pass')
            pass
