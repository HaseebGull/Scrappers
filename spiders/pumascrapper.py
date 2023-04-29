import sys
from pathlib import Path

DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(DIR.parent.parent.parent.parent))
__package__ = DIR.name

import django

django.setup()
from BaseClass import *
from scrapy import signals

store_url = sys.argv[4]


class PumaScrapper(Spider_BaseClass):
    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(PumaScrapper, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        return spider

    def GetProductUrls(self, response):
        category_nodes = response.xpath(
            "//ul[@role='menubar']/li/div[div/a/span[contains(text(),'Women') or contains(text(),'Men') or contains(text(),'Kids') or contains(text(),'Sale')]]")
        for category_node in category_nodes:
            category_title = category_node.xpath("./div/a/span/text()").get().strip()
            print("top_category_title :", category_title)
            sub_category_nodes = category_node.xpath(
                ".//div[@data-test-id='secondary-nav-menu']/div/ul/li/a[contains(text(),'Dresses') or contains(text(),'Loungewear') or contains(text(),'Matching')]")
            for sub_category_node in sub_category_nodes:
                sub_category_title = sub_category_node.xpath("./text()").get().strip()
                sub_category_link = sub_category_node.xpath("./@href").get()
                if not sub_category_link.startswith(store_url):
                    sub_category_link = store_url.rstrip('/us/en') + sub_category_link
                print(sub_category_title, " :", sub_category_link)
                category = category_title + " " + sub_category_title
                self.listing(sub_category_link, category)
        return Spider_BaseClass.AllProductUrls

    def listing(self, sub_category_link, category):
        subCategoryLinkResponse = requests.get(sub_category_link)
        subCategoryLinkResponse = HtmlResponse(url=sub_category_link, body=subCategoryLinkResponse.text,
                                               encoding='utf-8')
        total_products = subCategoryLinkResponse.xpath("//nav[@aria-label='Layout']/div/span/text()").get().strip()
        listing_page = sub_category_link + "?offset=" + str(total_products)
        listing_page_response = HtmlResponse(url=listing_page, body=subCategoryLinkResponse.text, encoding='utf-8')
        product_list = listing_page_response.xpath("//li[@data-test-id='product-list-item']/div/a/@href").extract()
        for productUrl in product_list:
            if not productUrl.startswith(store_url):
                productUrl = store_url.rstrip('/') + productUrl
            print('PRODUCT URL :', productUrl)
            Spider_BaseClass.AllProductUrls.append(productUrl)
            siteMapCategory = str(Spider_BaseClass.ProductUrlsAndCategory.get(productUrl)).replace('None', '')
            if siteMapCategory:
                Spider_BaseClass.ProductUrlsAndCategory[productUrl] = siteMapCategory + " " + category
            else:
                Spider_BaseClass.ProductUrlsAndCategory[productUrl] = category

    def GetProducts(self, response):
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
        color = self.GetSelectedColor(response)
        name = str(response.xpath("//h1[contains(@id,'title')]/text()").get()).strip()
        if not color == '' and not re.search(color, name, re.I):
            name = name + " - " + color
        print("name =", name)
        return name

    def GetSelectedColor(self, response):
        color = str(response.xpath("//div[@class='colour-option-label']/p/span[2]/text()").get()).strip()
        return color