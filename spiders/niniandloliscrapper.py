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


class NiniandLoliScrapper(shopify):
    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(NiniandLoliScrapper, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        return spider

    def GetProductUrls(self, homePageResponse):
        # ========== Category And Subcategory ==========#
        topCategoryNodes = homePageResponse.xpath(
            "//ul[contains(@class,'menu-navigation__list')]/li[contains(span/text(),'Shop by Category')]")
        for topCategoryNode in topCategoryNodes:
            topCategoryTitle = topCategoryNode.xpath("./span/text()").get().strip()
            # /div/ul/li[span/span/text()='Girl Apparel' or span/span/text()='Boy Apparel']
            categoryNodes = topCategoryNode.xpath(
                "./div/ul/li[span/span/text()='Girl Apparel' or span/span/text()='Boy Apparel']")
            for categoryNode in categoryNodes:
                categoryTitle = categoryNode.xpath("./span/span/text()").get().strip()
                subCategoryJsonStr = categoryNode.xpath("./span/@data-childs").get()
                subCategoryJson = json.loads(subCategoryJsonStr)
                if subCategoryJson[0]['featured_identifier'] == " " + categoryTitle + "":
                    if subCategoryJson[0]['childs']:
                        for subCategory in subCategoryJson[0]['childs']:
                            if subCategory['name'] == 'Gowns' or subCategory['name'] == 'Dresses' or subCategory[
                                'name'] == 'Footies' or subCategory['name'] == 'Onesies' or subCategory[
                                'name'] == 'Overalls, Playsuits & Rompers' or subCategory['name'] == 'Sets' or \
                                    subCategory['name'] == 'Sleepwear' or subCategory['name'] == 'Sunsuit':
                                subCategoryTitle = subCategory['name']
                                subCategoryLink = subCategory['url']
                                # =================== BREADCRUM ===================3
                                category = topCategoryTitle + " " + categoryTitle + " " + subCategoryTitle
                                # ======================================#
                                self.listing(subCategoryLink, category)
        return Spider_BaseClass.AllProductUrls

    def listing(self, categorylink, category):
        CategoryLinkResponse = requests.get(categorylink)
        categoryPageResponse = HtmlResponse(url=categorylink, body=CategoryLinkResponse.text, encoding='utf-8')
        product_list = categoryPageResponse.xpath(
            "//h3[contains(@class,'product-title')]/a/@href").extract()
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
                categoryPageResponse.xpath("//link[@rel='next']/@href").extract()[0]
            if not nextpageUrl.startswith(store_url):
                nextpageUrl = store_url.rstrip('/') + nextpageUrl
            self.listing(nextpageUrl, category)
        except:
            pass

    def GetName(self, response):
        color = self.GetSelectedColor(response)
        name = shopify.GetName(self, response)
        if not color == '' and not re.search(color, name):
            name = name + ' - ' + color
        return name

    def GetSelectedColor(self, response):
        try:
            return response.xpath("//h4[@class='swatch__title' and contains(text(),'Color')]/span/text()").get().strip()
        except:
            return ''

    def IgnoreProduct(self, response):
        if re.search('"availability" :', response.text):
            productAvailability = response.text.split('"availability" :')[1].split(',')[0].strip()
            if not 'InStock' in productAvailability:
                return True
            else:
                return False
