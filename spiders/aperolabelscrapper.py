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


class AperolabelScrapper(shopify):
    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(AperolabelScrapper, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        return spider

    def GetProductUrls(self, homePageResponse):
        top_category_nodes = homePageResponse.xpath("//div[@id='main-nav']//ul/li[a[contains(text(),'SHOP')]]")
        for top_category_node in top_category_nodes:
            top_category_title = top_category_node.xpath('./a/text()').get().strip()
            top_category_link = top_category_node.xpath('./a/@href').get()
            if not top_category_link.startswith(store_url):
                top_category_link = store_url.rstrip('/') + top_category_link
            print(top_category_title, ":", top_category_link)

            category_nodes = top_category_node.xpath(
                "./div/ul[@class='navigation__tier-2']/li/a[contains(text(),'DRESSES') or contains(text(),'NEW ARRIVALS') or contains(text(),'Sale')]")
            for category_node in category_nodes:
                category_title = category_node.xpath('./text()').get().strip()
                category_link = category_node.xpath('./@href').get()
                if not category_link.startswith(store_url):
                    category_link = store_url.rstrip('/') + category_link
                print(category_title, " ", category_link)
                category = 'Women' + " " + top_category_title + " " + category_title
                self.listing(category_link, category)

        return Spider_BaseClass.AllProductUrls

    def listing(self, categorylink, category):
        CategoryLinkResponse = requests.get(categorylink)
        categoryPageResponse = HtmlResponse(url=categorylink, body=CategoryLinkResponse.text, encoding='utf-8')

        product_list = categoryPageResponse.xpath(
            "//div[@class='product-info']//a[@class='product-link']/@href").extract()
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
            nextpageUrl = categoryPageResponse.xpath("//a[@class='next']/@href").extract()[0]
            if not nextpageUrl.startswith(store_url):
                nextpageUrl = store_url.rstrip('/') + nextpageUrl
            self.listing(nextpageUrl, category)
        except:
            pass

    def GetProducts(self, response):
        ignorProduct = self.IgnoreProduct(response)
        if ignorProduct == True:
            self.ProductIsOutofStock(GetterSetter.ProductUrl)
        else:
            shopify.productJson = json.loads(self.SetProductJson(response))
            categoryAndName = shopify.GetCategory(self, response) + " " + self.GetName(response)
            if (re.search('sale', categoryAndName, re.IGNORECASE) or
                re.search('new arrival', categoryAndName, re.IGNORECASE)) and not \
                    re.search(r'\b((shirt(dress?)|jump(suit?)|dress|gown|suit|caftan)(s|es)?)\b', categoryAndName,
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
        color = response.xpath(
            "//h1[@class='title']/text()").get().strip().split('-')[1]
        return color

    def IgnoreProduct(self, response):
        if re.search('"availability":', response.text):
            productAvailability = response.text.split('"availability":')[1].split(',')[0].strip()
            if not 'InStock' in productAvailability:
                return True
            else:
                return False
