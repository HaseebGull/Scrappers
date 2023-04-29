import json
import sys
from pathlib import Path

DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(DIR.parent.parent.parent.parent))
__package__ = DIR.name

import django

django.setup()
from scrapy import signals
from Shopify import *

store_url = sys.argv[4]


class AngelDearScrapper(shopify):
    Spider_BaseClass.testingGender = 'Baby'

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(AngelDearScrapper, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        return spider

    # topCategoryLink = topNode['setting']['url']['link']
    def GetProductUrls(self, homePageResponse):
        # ========== Category And Subcategory ==========#
        navJsonStr = homePageResponse.xpath("//script[@id='qikify-smartmenu-data']/text()").get()
        navJson = json.loads(navJsonStr)

        topNodes = navJson['megamenu']
        for topNode in topNodes:
            if topNode['setting']['title'] == 'New Arrivals' or topNode['setting']['title'] == 'Shop by Style' or \
                    topNode['setting']['title'] == 'Shop by Theme' or topNode['setting']['title'] == 'Sale':
                topCategoryTitle = topNode['setting']['title']
                categoryNodes = topNode['menus']

                if len(topNode['menus']) == 0:
                    topCategoryLink = topNode['setting']['url']['collection']['handle']
                    if not topCategoryLink.startswith(store_url):
                        topCategoryLink = store_url + "collections/" + topCategoryLink
                    category = 'Baby Boy ' + 'Baby Girl ' + topCategoryTitle
                    self.listing(topCategoryLink, category)
                else:
                    for categoryNode in categoryNodes:
                        if categoryNode['setting']['title'] == 'Collections' or \
                                categoryNode['setting']['title'] == 'Sizes':
                            categoryTitle = categoryNode['setting']['title']
                            subCategoryNodes = categoryNode['menus']
                            for subCategoryNode in subCategoryNodes:
                                settingToken = subCategoryNode['setting']
                                if settingToken.get('title') is not None:
                                    try:
                                        subCategoryTitle = settingToken['title']
                                        subCategoryLink = settingToken['url']['collection']['handle']
                                    except:
                                        if settingToken['collection']['title'] == 'Top' or \
                                                settingToken['collection']['title'] == 'Undies':
                                            continue
                                        else:
                                            subCategoryTitle = settingToken['collection']['title']
                                            subCategoryLink = settingToken['collection']['handle']

                                    if not subCategoryLink.startswith(store_url):
                                        subCategoryLink = store_url + "collections/" + subCategoryLink
                                    category = 'Baby Boy ' + 'Baby Girl ' + topCategoryTitle + " " + categoryTitle + " " + subCategoryTitle
                                    self.listing(subCategoryLink, category)
        return Spider_BaseClass.AllProductUrls

    def listing(self, categorylink, category):
        CategoryLinkResponse = requests.get(categorylink)
        categoryPageResponse = HtmlResponse(url=categorylink, body=CategoryLinkResponse.text, encoding='utf-8')
        product_list = categoryPageResponse.xpath("//div[contains(@class,'product__content')]/a/@href").extract()
        for productUrl in product_list:
            if not productUrl.startswith(store_url):
                productUrl = store_url.rstrip('/') + productUrl
            productUrl = self.GetCanonicalUrl(productUrl)
            Spider_BaseClass.AllProductUrls.append(productUrl)
            siteMapCategory = str(Spider_BaseClass.ProductUrlsAndCategory.get(productUrl)).replace('None', '')
            if siteMapCategory:
                Spider_BaseClass.ProductUrlsAndCategory[productUrl] = siteMapCategory + " " + category
            else:
                Spider_BaseClass.ProductUrlsAndCategory[productUrl] = category
        try:
            nextpageUrl = \
                categoryPageResponse.xpath("//link[@rel='next']/@href").get()
            if not nextpageUrl.startswith(store_url):
                nextpageUrl = store_url.rstrip('/') + nextpageUrl
            self.listing(nextpageUrl, category)
        except:
            pass

    def GetProducts(self, response):
        ignorProduct = self.IgnoreProduct(response)
        if ignorProduct == True:
            self.ProductIsOutofStock(GetterSetter.ProductUrl)
        shopify.productJson = json.loads(self.SetProductJson(response))
        categoryAndName = shopify.GetCategory(self, response) + " " + self.GetName(response)
        if (re.search('Sale', categoryAndName, re.IGNORECASE) or
            re.search('New Arrivals', categoryAndName, re.IGNORECASE)) and not \
                re.search(
                    r'\b((shirt(dress?)|jump(suit?)|body(suit?)|sun(suit?)|dress|loungewear|romper|gown|FOOTIE|overall|suit|top and bloomer|set|caftan)(s|es)?)\b',
                    categoryAndName,
                    re.IGNORECASE):
            print('Skipping Non Dress Product')
            self.ProductIsOutofStock(GetterSetter.ProductUrl)
        else:
            self.GetProductInfo(response)

    def GetSizes(self, response):
        sizeList = []
        sizes = shopify.GetSizes(self, response)
        name = shopify.GetName(self, response)
        if re.search("-", name):
            color = str(name).split('-')[1].strip()
        else:
            color = ''
        for size in sizes:
            sizeList.append([color, size[1], size[2], size[3], size[4], size[5]])
        return sizeList

    def IgnoreProduct(self, response):
        if re.search('"availability":', response.text):
            productAvailability = response.text.split('"availability":')[1].split(',')[0].strip()
            if not 'InStock' in productAvailability:
                return True
            else:
                return False
