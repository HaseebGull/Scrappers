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


class WaverlyBoutiqueScraper(shopify):
    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(WaverlyBoutiqueScraper, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        return spider

    def GetProductUrls(self, homePageResponse):
        # ========== Category And Subcategory ==========#
        topCategoryNodes = homePageResponse.xpath(
            "//header[@class='site-header']/div/div[@class='text-center']/ul/li/a[contains(text(),'NEW ARRIVALS') or contains(text(),'DRESSES')"
            "or contains(text(),'JUMPERS') or contains(text(),'SALE') or contains(text(),'BABY + KIDS GIRLS')"
            "or contains(text(),'BABY + KIDS BOY')"
            "or contains(text(),'NEW BABY + KIDS ARRIVALS')]")
        for topCategoryNode in topCategoryNodes:
            topCategoryTitle = topCategoryNode.xpath("./text()").get().strip()
            topCategorylink = topCategoryNode.xpath("./@href").get()
            if not topCategorylink.startswith(store_url):
                topCategorylink = store_url.rstrip('/') + topCategorylink
            if topCategoryTitle == 'DRESSES' or topCategoryTitle == 'JUMPERS' or topCategoryTitle == 'SALE' or topCategoryTitle == 'NEW ARRIVALS':
                category = 'Women ' + topCategoryTitle
            else:
                category = topCategoryTitle
            self.listing(topCategorylink, store_url, category)
        return Spider_BaseClass.AllProductUrls

    def listing(self, topCategorylink, store_url, category):
        topCategoryLinkResponse = requests.get(topCategorylink)
        topCategoryLinkResponse = HtmlResponse(url=topCategorylink, body=topCategoryLinkResponse.text, encoding='utf-8')
        product_list = topCategoryLinkResponse.xpath(
            "//a[contains(@class,'grid-product__link ')]/@href").extract()
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
            nextpage = \
                topCategoryLinkResponse.xpath("//div[@class='pagination']/span[@class='page']/a/@href").extract()[0]
            if not nextpage.startswith(store_url):
                nextpage = store_url.rstrip('/') + nextpage
            nextpageresponse = requests.get(nextpage)
            nextpageresponse = HtmlResponse(url=nextpage, body=nextpageresponse.text, encoding='utf-8')
            self.listing(nextpageresponse, category, store_url)
        except:
            pass

    def GetProducts(self, response):
        ignorProduct = self.IgnoreProduct(response)
        if ignorProduct == True:
            self.ProductIsOutofStock(GetterSetter.ProductUrl)
        shopify.productJson = json.loads(self.SetProductJson(response))
        categoryAndName = shopify.GetCategory(self, response) + " " + self.GetName(response)
        if (re.search('SALE', categoryAndName, re.IGNORECASE) or
            re.search('NEW BABY \+ KIDS ARRIVALS', categoryAndName, re.IGNORECASE) or
            re.search('BABY \+ KIDS BOY', categoryAndName, re.IGNORECASE) or
            re.search('BABY \+ KIDS GIRLS', categoryAndName, re.IGNORECASE) or
            re.search('NEW ARRIVALS', categoryAndName, re.IGNORECASE)) and not re.search(
            r'\b((shirt(dress?)|jump(suit?)|dress|gown|suit|romper|sleeper|caftan)(s|es)?)\b', categoryAndName,
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
