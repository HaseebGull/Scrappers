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


class BabycottonsScrapper(shopify):
    Spider_BaseClass.testingGender = 'Kids'
    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(BabycottonsScrapper, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        return spider

    def GetProductUrls(self, homePageResponse):
        # ========== Category And Subcategory ==========#

        topCategoryNodes = homePageResponse.xpath(
            "//ul[@id='nt_main_menu']/li[a[contains(text(),'shop by age') or contains(text(),'shop by product') or contains(text(),'sale')]]")
        for topCategoryNode in topCategoryNodes:
            topCategoryTitle = topCategoryNode.xpath("./a/text()").get().strip()
            topCategorylink = topCategoryNode.xpath("./a/@href").get()
            if not topCategorylink.startswith(store_url):
                topCategorylink = store_url.rstrip('/') + topCategorylink

            categoryNodes = topCategoryNode.xpath(
                "./div/div//ul/li/a[contains(text(),'baby') or contains(text(),'toddler') or contains(text(),'kid')  or contains(text(),'sleepwear') or contains(text(),'bodysuits') or contains(text(),'one piece') or contains(text(),'dress')]")
            if not categoryNodes:
                category = topCategoryTitle
                self.listing(topCategorylink, category)
            for categoryNode in categoryNodes:
                categoryTitle = categoryNode.xpath("./text()").get().strip()
                categorylink = categoryNode.xpath("./@href").get()
                if not categorylink.startswith(store_url):
                    categorylink = store_url.rstrip('/') + categorylink
                if categoryNode and topCategoryTitle == 'shop by age' and categoryTitle == 'baby - preemie to 24m' \
                        or categoryTitle == 'toddler - 3t to 4t' or categoryTitle == 'kid - 6 to 10 years':
                    topCategoryLinkResponse = requests.get(topCategorylink)
                    topCategoryLinkResponse = HtmlResponse(url=topCategorylink, body=topCategoryLinkResponse.text,
                                                           encoding='utf-8')
                    subCategoryNodes = topCategoryLinkResponse.xpath(
                        "//div[contains(@id,'sidebar_shop')]/div/aside/h3[contains(text(),'category')]/following-sibling::div/ul/li/a[contains(text(),'sleepwear') or contains(text(),'bodysuits') or contains(text(),'one piece') or contains(text(),'dress')]")
                    if not subCategoryNodes:
                        category = topCategoryTitle + " " + categoryTitle
                        self.listing(categorylink, category)
                    else:
                        for subCategoryNode in subCategoryNodes:
                            subCategoryTitle = subCategoryNode.xpath("./text()").get().strip()
                            subCategorylink = subCategoryNode.xpath("./@href").get()
                            if not subCategorylink.startswith(store_url):
                                subCategorylink = store_url.rstrip('/') + subCategorylink
                            category = topCategoryTitle + " " + categoryTitle + " " + subCategoryTitle
                            self.listing(subCategorylink, category)
                else:
                    category = topCategoryTitle + " " + categoryTitle
                    self.listing(categorylink, category)
        return Spider_BaseClass.AllProductUrls

    def listing(self, categorylink, category):
        CategoryLinkResponse = requests.get(categorylink)
        categoryPageResponse = HtmlResponse(url=categorylink, body=CategoryLinkResponse.text, encoding='utf-8')
        product_list = categoryPageResponse.xpath("//div[contains(@class,'product-info-wrap')]/div/a/@href").extract()
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
        if (re.search('sale', categoryAndName, re.IGNORECASE)) and not \
                re.search(r'\b((shirt(dress?)|jump(suit?)|dress|gown|set|footie|romper|footed pajama|overall|body(suit?)|suit|caftan)(s|es)?)\b', categoryAndName,
                          re.IGNORECASE):
            print('Skipping Non Dress Product')
            self.ProductIsOutofStock(GetterSetter.ProductUrl)
        else:
            self.GetProductInfo(response)

    def IgnoreProduct(self, response):
        if re.search('"availability":', response.text):
            productAvailability = response.text.split('"availability":')[1].split(',')[0].strip()
            if not 'InStock' in productAvailability:
                return True
            else:
                return False
