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


class ChichiScraper(shopify):
    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(ChichiScraper, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        return spider

    def GetProductUrls(self, homePageResponse):
        # ========== Category And Subcategory ==========#
        navJsonStr = homePageResponse.xpath("//script[@id='qikify-smartmenu-data']/text()").get()
        navJson = json.loads(navJsonStr)

        topNodes = Enumerable(navJson['megamenu']).where(
            lambda x: x['setting']['title'] == 'Dresses' or x['setting']['title'] == 'The Wedding Hub' or x['setting'][
                'title'] == 'Clothing' or x['setting'][
                          'title'] == 'New In' or x['setting']['title'] == 'Girls' or x['setting'][
                          'title'] == 'Sale & Offers').to_list()
        for topNode in topNodes:
            topcategoryTitle = topNode['setting']['title']
            topcategoryUrl = 'collections' + '/' + topNode['setting']['url']['collection']['handle']
            if not topcategoryUrl.startswith(store_url):
                topcategoryUrl = store_url + topcategoryUrl

            # ==============================  Category  ================================= #

            categoryNodes = topNode['menus']
            for categoryNode in categoryNodes:
                categoryTitle = categoryNode['setting']['title']
                if re.search('dress', categoryTitle, re.IGNORECASE) or \
                        re.search('Bride', categoryTitle, re.IGNORECASE) or \
                        re.search('Clothing by Occasion', categoryTitle, re.IGNORECASE) or \
                        re.search('Clothing by Category', categoryTitle, re.IGNORECASE):
                    if not categoryNode['menus']:
                        categoryLink = 'collections' + '/' + categoryNode['setting']['url']['collection']['handle']
                        if not categoryLink.startswith(store_url):
                            categoryLink = store_url + categoryLink
                    else:
                        # ==============================  SUB Category  ================================= #
                        subCategoryNodes = categoryNode['menus']
                        if subCategoryNodes:
                            for subCategoryNode in subCategoryNodes:
                                subCategoryTitle = subCategoryNode['setting']['title']
                                if re.search('dress', subCategoryTitle, re.IGNORECASE) or \
                                        re.search('jumpsuit', subCategoryTitle, re.IGNORECASE) or \
                                        re.search('Dresses', subCategoryTitle, re.IGNORECASE) or \
                                        re.search('suits', subCategoryTitle, re.IGNORECASE) or \
                                        re.search('sets', subCategoryTitle, re.IGNORECASE) or \
                                        re.search('nightwear', subCategoryTitle, re.IGNORECASE) or \
                                        re.search('occasionwear', subCategoryTitle, re.IGNORECASE) or \
                                        re.search('Partywear', subCategoryTitle, re.IGNORECASE) or \
                                        re.search('workwear', subCategoryTitle, re.IGNORECASE):
                                    subCategoryLink = 'collections' + '/' + \
                                                      subCategoryNode['setting']['url']['collection'][
                                                          'handle']
                                    if not subCategoryLink.startswith(store_url):
                                        subCategoryLink = store_url + subCategoryLink
                                    category = 'Women ' + topcategoryTitle + " " + categoryTitle + " " + subCategoryTitle
                                    self.listing(subCategoryLink, category)
                        else:
                            category = 'Women ' + topcategoryTitle + " " + categoryTitle
                            self.listing(categoryLink, category)
        return Spider_BaseClass.AllProductUrls

    def listing(self, categorylink, category):
        CategoryLinkResponse = requests.get(categorylink)
        categoryPageResponse = HtmlResponse(url=categorylink, body=CategoryLinkResponse.text, encoding='utf-8')
        product_list = categoryPageResponse.xpath(
            "//a[contains(@class,'ProductItem__ImageWrapper')]/@href").extract()
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
                categoryPageResponse.xpath("//a[@rel='next']/@href").get()
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
        if (re.search('Workwear', categoryAndName, re.IGNORECASE) or
            re.search('Sets & Co-ords', categoryAndName, re.IGNORECASE)) and not \
                re.search(r'\b((shirt(dress?)|jump(suit?)|dress|set|gown|suit|caftan)(s|es)?)\b', categoryAndName,
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
            "//div[@class='ProductMeta']/p[contains(text(),'colour')]/span/text()").get().strip()

    def IgnoreProduct(self, response):
        if re.search('"availability":', response.text):
            productAvailability = response.text.split('"availability":')[1].split(',')[0].strip()
            if not 'InStock' in productAvailability:
                return True
            else:
                return False
