import json
import re
import sys
from pathlib import Path
import requests
from WebDriver import SeleniumResponse
DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(DIR.parent.parent.parent.parent))
__package__ = DIR.name
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

import django

django.setup()
from Shopify import *
from BaseClass import Spider_BaseClass
from scrapy import signals

store_url = sys.argv[4]


# //header[(@data-hook="site-header")]/div/section[2]/div[div[3]/a/text() or div[4]/div[div[1]/span/a/text() or div[2]/span/a/text() or div[3]/span/a/text() or div[5]/span/a/text() or div[6]/span/a/text() or div[7]/span/a/text() ] ]
class SsenseScrapper(Spider_BaseClass):
    Spider_BaseClass.cookiesDict = {"currency": "USD", "currencyOverride": "USD"}
    Spider_BaseClass.hasDriver = True

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(SsenseScrapper, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        return spider

    def GetProductUrls(self, response):
        response = SeleniumResponse(store_url)
        top_category_nodes = response.xpath(
            "//nav[@role='navigation']/ul/li/a[contains(text(),'Menswear') or contains(text(),'Womenswear') or contains(text(),'sale')]")
        for top_category_node in top_category_nodes:
            top_category_title = top_category_node.xpath("./text()").get().strip()
            top_category_link = top_category_node.xpath("./@href").get()
            if not top_category_link.startswith(store_url):
                top_category_link = store_url.rstrip('/') + top_category_link
            print("top_category_title : ", top_category_link)
            get_request = requests.get(top_category_link)
            top_category_node = HtmlResponse(url=top_category_link,body=get_request.text,encoding='utf-8')
            category_nodes = top_category_node.xpath("//div[@id='category-list']/ul/li/a[contains(text(),'CLOTHING')]")
            print(category_nodes)
            for category_node in category_nodes:
                category_title = category_node.xpath("./text()").get().strip()
                category_link = category_node.xpath("./@href").get()
                print("category_title : ", category_title)
                if not category_link.startswith(store_url):
                    category_link = store_url.rstrip('/') + category_link
                sub_category_nodes = category_node.xpath(
                    "//ul[@class='sublevel']/li/a[contains(text(),'Suits') or contains(text(),'suits') or contains(text(),'Dress')]")
                for sub_category_node in sub_category_nodes:
                    sub_category_title = sub_category_node.xpath("./text()").get().strip()
                    sub_category_link = sub_category_node.xpath("./@href").get().strip()
                    if not sub_category_link.startswith(store_url):
                        sub_category_link = store_url.rstrip('/') + sub_category_link
                    print("sub_category_title : ", sub_category_title)
                    category = top_category_title+" "+category_title+" "+sub_category_title
                    self.listing(sub_category_link,category)
        return Spider_BaseClass.AllProductUrls

    def listing(self, response,category):
        self.GetUrls(response, category)
        # listingproduct_urls = response.xpath("//div[@class='plp-products__product-tile']/div/a")
        # for product_urls in listingproduct_urls:
        #     product_url = product_urls.xpath("./@href").get()
        #     if not product_url.startswith(store_url):
        #         product_url = store_url + product_url
        #     print("product_url : ", product_url)
            # try:
            #     next_url=CategoryLinkResponse.xpath("//li[@class='pagination__item']/a[ not(contains(@data-test,'plpPagination'))]/@href").get()
            #     yield scrapy.Request(url=product_url, callback=self.listing)
            # except:
            #     pass
    def GetUrls(self, CategoryLinkResponse, category):
        product_list = CategoryLinkResponse.xpath("//div[@class='plp-products__product-tile']/div/a/@href").extract()
        for productUrl in product_list:
            if not productUrl.startswith(store_url):
                productUrl = store_url.rstrip('/') + productUrl
            print("productUrl : ",productUrl )
            Spider_BaseClass.AllProductUrls.append(productUrl)
            siteMapCategory = str(Spider_BaseClass.ProductUrlsAndCategory.get(productUrl)).replace('None', '')
            if siteMapCategory:
                Spider_BaseClass.ProductUrlsAndCategory[productUrl] = siteMapCategory + " " + category
            else:
                Spider_BaseClass.ProductUrlsAndCategory[productUrl] = category

    def GetProducts(self, response):
        if Spider_BaseClass.hasDriver:
            response=SeleniumResponse(response.url)
        ignorProduct = self.IgnoreProduct(response)
        if ignorProduct == True:
            self.ProductIsOutofStock(GetterSetter.ProductUrl)
        categoryAndName = self.GetCategory(response) + " " + self.GetName(response)
        if (re.search('Sale', categoryAndName, re.IGNORECASE) or
            re.search('New', categoryAndName, re.IGNORECASE)) and not \
                re.search(r'\b((shirt(dress?)|jump(suit?)|dress|set|gown|suit|caftan)(s|es)?)\b', categoryAndName,
                          re.IGNORECASE):
            print('Skipping Non Dress Product')
            self.ProductIsOutofStock(GetterSetter.ProductUrl)
        else:
            self.GetProductInfo(response)

    def GetName(self, response):
        # color = self.GetSelectedColor(response)
        name = str(response.xpath("//h2[@data-test='pdpProductNameText']/text()").get()).strip()
        # if not color == '' and not re.search(color, name):
        #     name = name + ' - ' + color
        print(name)


    def GetSelectedColor(self, response):
        colors = ''.join(response.xpath("//div[@class='s-row pdp-desktop__content']//p[@id='pdpProductDescriptionContainerText']/text()").extract())
        print(colors)
        color = str(colors).split("color:")[1].strip()
        return color

    def GetPrice(self, response):
        orignalPrice = response.xpath("//h2[@id='pdpSalePriceText']/text()").get()
        if orignalPrice:
            return float(str(orignalPrice).replace("$",'').replace("USD",'').strip())
        else:
            regularPrice = response.xpath("//h3[@id='pdpRegularPriceText']/text()").get()
            print(regularPrice)
            return float(str(regularPrice).replace("$",'').replace("USD",'').strip())

    def GetSalePrice(self, response):
        salePrice = response.xpath("//h3[@id='pdpRegularPriceText']/text()").get()
        if salePrice:
            return float(str(salePrice).replace("$",'').replace("USD",'').strip())
        else:
            return 0

    def GetDescription(self, response):
        return ''.join(response.xpath("//div[@class='s-row pdp-desktop__content']//p[@id='pdpProductDescriptionContainerText']/text()").extract())



    def GetBrand(self, response):
        return response.xpath("//img[@class='site-logo dark']/@alt").get()

    def GetImageUrl(self, response):
        # image_json = response.xpath("//script[@type='application/ld+json']/text()").get()
        # json_image = json.loads(image_json)
        return "json_image['image']"

    def GetSizes(self, response):
        sizes = []
        sizeList = response.xpath("//select[@aria-label='Size']/option[not(contains(@disabled,'disabled'))]")
        gender = ProductFilters.objects.get(ProductUrl=GetterSetter.ProductUrl).ParentCategory.split(',')[0]
        color = self.GetSelectedColor(response)
        for size in sizeList:
            sizename=size.xpath("./text()").get().strip()
            available = True
            fitType = GetFitType(gender, sizename)
            sizes.append((color, sizename, available, fitType, 0.0, 0.0))
        return sizes

    def GetCategory(self, response):
        siteMapCategory = str(Spider_BaseClass.ProductUrlsAndCategory.get(GetterSetter.ProductUrl)).replace('None', '')
        return 'Women '+siteMapCategory.strip()

