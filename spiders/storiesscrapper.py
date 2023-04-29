import sys
from pathlib import Path

import requests
import scrapy
from lxml import html
DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(DIR.parent.parent.parent.parent))
__package__ = DIR.name

import django

django.setup()
from BaseClass import *
from scrapy import signals

store_url = sys.argv[4]


class StoriesScrapper(Spider_BaseClass):
    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(StoriesScrapper, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        return spider

    def GetProductUrls(self, homePageResponse):
        # ========== Category And Subcategory ==========#
        topCategoryNodes = homePageResponse.xpath(
            "//div[@class='menu-content']/div[@class='primary']/ul/li[@data-category-id='cat_4']/a")
        for topCategoryNode in topCategoryNodes:
            topCategoryTitle = topCategoryNode.xpath("./text()").get().strip()
            topCategorylink = topCategoryNode.xpath("./@href").get()
            if not topCategorylink.startswith(store_url):
                topCategorylink = store_url.rstrip('/') + topCategorylink
            print("TOP CATEGORY  :", topCategoryTitle, "TOP CATEGORY LINK  :", topCategorylink)
            categoryNodes = topCategoryNode.xpath(
                "//ul[@class='subcategories']/li/a[contains(text(),' Dresses') or contains(text(),' Jumpsuits')]")
            for categoryNode in categoryNodes:
                categoryTitle = categoryNode.xpath("./text()").get().strip()
                categorylink = categoryNode.xpath("./@href").get()
                print("CATEGORY  :", categoryTitle, "CATEGORY LINK  :", categorylink)
                # CategoryLinkResponse = requests.get(categorylink)
                # CategoryLinkResponse = HtmlResponse(url=categorylink, body=CategoryLinkResponse.text, encoding='utf-8')
                self.listing(categorylink, categoryTitle)
        return Spider_BaseClass.AllProductUrls

    def listing(self, categorylink, categoryTitle):
        ajaxapi = 'https://www.stories.com/en_usd/clothing/dresses/_jcr_content/subdepartmentPar/productlisting_d5ab.products.html?start=20'
        ajaxResp = scrapy.Request(ajaxapi)
        # CategoryLinkResponse = HtmlResponse(url=ajaxapi, body=ajaxResp, encoding='utf-8')
        productList = ajaxResp.xpath("//div[@class='o-product producttile-wrapper']/a/@href").extract()
        for product in productList:
            print("Product URL : ", product)

    def GetName(self, response):

        name = response.xpath("//h1[contains(@class,'x-product-title--text')]/text()").get()
        return name

    def GetPrice(self, response):
        # price = response.xpath("//span[@id='price-value']/text()").get()
        # price = response.xpath("//s[@id='price-value-additional']/text()").get() #NONE
        orignalPrice = response.xpath(
            "//p[contains(@class,'__pricing')]/s[contains(@class,'pricing-original')]/text()").get()
        if orignalPrice != None:
            return orignalPrice
        else:
            orignalPrice = response.xpath(
                "//p[contains(@class,'__pricing')]/span[contains(@class,'pricing-current')]/text()").get()
            return orignalPrice

    def GetSalePrice(self, response):
        salePrice = response.xpath(
            "//p[contains(@class,'__pricing')]/span[contains(@class,'pricing-current')]/text()").get()
        if salePrice != None:
            return salePrice
        else:
            return 0

    def GetBrand(self, response):
        brand = response.xpath("//div[contains(@class,'t-product--brand')]/a/text()").get()
        return brand

    def GetImageUrl(self, response):
        imageUrls = []
        images = response.xpath("//div[contains(@class,'product-images--image swiper-slide')]/div/img/@src").extract()
        for imageurl in images:
            imageUrls.append(store_url.rstrip('/') + imageurl)
        return imageUrls

    def GetDescription(self, response):
        desNode = response.xpath("//div[contains(@id,'tab-descrip')]/text()").extract()
        description = ' '.join(map(str, desNode))
        return description

    def GetSizes(self, response):
        pass

    # def GetCategory(self, response):
    #     filterList = []
    #     if GetterSetter.ProductUrl in Spider_BaseClass.ProductUrlsAndCategory:
    #         categories = Spider_BaseClass.ProductUrlsAndCategory[GetterSetter.ProductUrl]
    #         for category in str(categories).split('$'):
    #             filterList.append(category)
    #
    #     for filter in shopify.ProductJson['tags']:
    #         filterList.append(filter)
    #     filters = '$'.join(map(str, filterList))
    #     return filters
