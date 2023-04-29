import json
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


class AnthropologieScrapper(Spider_BaseClass):
    Spider_BaseClass.cookiesDict = {"currency": "USD", "currencyOverride": "USD"}
    Spider_BaseClass.hasDriver = True

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(AnthropologieScrapper, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        return spider

    def GetProductUrls(self, homePageResponse):
        category_nodes = homePageResponse.xpath(
            "(//ul[@aria-label='Main Navigation']/li/div/a[contains(text(),'Dresses') or contains(text(),'Clothing') or contains(text(),'Sale')])[1]")
        for category_node in category_nodes:
            category_title = category_node.xpath('./text()').get().strip()
            print("Category: ", category_title)
            category_link = category_node.xpath('./@href').get()
            if not category_link.startswith(store_url):
                category_link = store_url + category_link
            category_page_response = SeleniumResponse(category_link)
            sub_category_nodes = category_page_response.xpath(
                "(//ul[@class='c-pwa-left-navigation__list']/li//div/a[contains(text(),'Dresses') or contains(text(),'Wedding') or contains(text(),'Jumpsuits') or contains(text(),'loungewear') or contains(text(),'Sets') or contains(text(),'Clothing')])[1]")
            for sub_category_node in sub_category_nodes:
                sub_category_title = str(sub_category_node.xpath('./text()').get()).strip()
                sub_category_link = sub_category_node.xpath('./@href').get()
                if not sub_category_link.startswith(store_url):
                    sub_category_link = store_url + sub_category_link
                category = category_title + " " + sub_category_title
                print(sub_category_title, ":", sub_category_link)
                self.listing(sub_category_link, category)
        return Spider_BaseClass.AllProductUrls

    def listing(self, sub_category_link, category):
        seleniumResponse = SeleniumResponse(sub_category_link)
        json_str = '{"parentNavItem' + \
                   str(seleniumResponse.text).split(r'parentNavItem')[1].split(r'}", freezeReviver')[0]
        json_str = (re.sub(r'\\', "", json_str))
        listing_json = json.loads(json_str)
        current_page = listing_json["category"]["tileGrid"]["currentPage"]
        category_name = listing_json["category"]["slug"]
        total_pages = listing_json["category"]["tileGrid"]["totalPages"]
        for product_url in listing_json["category"]["tileGrid"]["pages"][str(current_page)]["wrapper"]["tiles"]:
            product_slug = product_url["product"]["productSlug"]
            for color_code in product_url["product"]["facets"]["colors"]:
                color_code = color_code["colorId"]
                product_url = store_url + "shop/" + product_slug + "?color=" + color_code
                Spider_BaseClass.AllProductUrls.append(product_url)
                siteMapCategory = str(Spider_BaseClass.ProductUrlsAndCategory.get(product_url)).replace('None', '')
                if siteMapCategory:
                    Spider_BaseClass.ProductUrlsAndCategory[product_url] = siteMapCategory + " " + category
                else:
                    Spider_BaseClass.ProductUrlsAndCategory[product_url] = category
        current_page += 1
        while current_page <= total_pages:
            next_page_url = store_url + "/" + category_name + "?page=" + str(current_page)
            self.listing(next_page_url, category)
            current_page += 1

    def GetProducts(self, response):
        if Spider_BaseClass.hasDriver:
            response = SeleniumResponse(response.url)

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
        name = str(response.xpath("//h1[contains(@class,'heading')]/text()").get()).strip()
        if not color == '' and not re.search(color, name, re.I):
            name = name + " - " + color
        print("name =", name)
        return name

    def GetSelectedColor(self, response):
        color = str(response.xpath("//span[contains(@class,'color-value')]/text()").get()).strip()
        return color

    def GetPrice(self, response):
        orignalPrice = response.xpath(
            "//p[@class='c-pwa-product-price']//span[contains(@class,'price__original')]/text()").get()
        if orignalPrice != None:
            return float(str(orignalPrice).strip().replace('$', '').replace(',', ''))
        else:
            regularPrice = response.xpath(
                "//p[@class='c-pwa-product-price']//span[contains(@class,'price__current')]/text()").get()
            return float(str(regularPrice).strip().replace('$', '').replace(',', ''))

    def GetSalePrice(self, response):
        salePrice = response.xpath(
            "//p[@class='c-pwa-product-price']//span[contains(@class,'price__current')]/text()").get()
        if salePrice != None:
            return float(str(salePrice).strip().replace('$', '').replace(',', ''))
        else:
            return 0

    def GetBrand(self, response):
        return str(response.xpath("//a[contains(@class,'product-partner')]/text()").get()).strip()

    def GetImageUrl(self, response):
        imageUrls = []
        images = response.xpath("//img[contains(@class,'image-viewer_')]/@src").extract()
        for image in images:
            imageUrls.append(image)
        return imageUrls

    def GetDescription(self, response):
        return ' '.join(response.xpath("//div[contains(@class,'product-details')]/div//text()").extract()).strip()

    def GetSizes(self, response):
        sizes = []
        gender = ProductFilters.objects.get(ProductUrl=GetterSetter.ProductUrl).ParentCategory.split(',')[0]
        json_str = str(response.text).split(r'"},\"primarySlice\":')[1].split(r']},\"afterpay\":')[0] + ']}'
        json_str = (re.sub(r'\\', "", json_str))
        size_json = json.loads(json_str)
        for size_list in size_json["sliceItems"]:
            color = size_list["displayName"]
            for size in size_list["includedSkus"]:
                avalaible_stock = size["stockLevel"]
                size_name = size["size"]
                if avalaible_stock != 0:
                    sizes.append((color, size_name, gender, 0.0, 0.0))
        return sizes

    def GetCategory(self, response):
        return "Women " + str(Spider_BaseClass.ProductUrlsAndCategory.get(GetterSetter.ProductUrl)).replace('None', '')
