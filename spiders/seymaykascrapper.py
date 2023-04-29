import json
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


class SeymaykaScrapper(shopify):
    global product_json
    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(SeymaykaScrapper, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        return spider

    def GetProductUrls(self, response):
        top_category_nodes = response.xpath(
            "(//ul[contains(@class,'site-navigation')]/li[a[contains(text(),'Men') or contains(text(),'Women')]])[1]")
        for top_category_node in top_category_nodes:
            top_category_title = top_category_node.xpath("./a/text()").get().strip()
            print("Top Title :", top_category_title)
            category_nodes = top_category_node.xpath(
                "(./div//div[@class='h5'][a[contains(text(),'CLOTHING')]])[1]")
            for category_node in category_nodes:
                category_title = category_node.xpath("./a/text()").get().strip()
                print("CategoryTitle :", category_title)
                sub_category_nodes = category_node.xpath(
                    "(./following-sibling::div/a[contains(text(),'Dresses') or contains(text(),'Sweaters') or "
                    "contains(text(),'Trousers')])[1]")
                for sub_category_node in sub_category_nodes:
                    sub_category_title = sub_category_node.xpath("./text()").get().strip()
                    sub_category_link = sub_category_node.xpath("./@href").get()
                    if not sub_category_link.startswith(store_url):
                        sub_category_link = store_url.rstrip('/') + sub_category_link
                    if top_category_title != 'Women' or sub_category_title != 'Trousers':
                        print(sub_category_title, " :", sub_category_link)
                        category = top_category_title + " " + category_title + " " + sub_category_title
                        self.listing(sub_category_link, category)
        return Spider_BaseClass.AllProductUrls

    def listing(self, sub_category_link, category):
        subCategoryLinkResponse = requests.get(sub_category_link)
        subCategoryLinkResponse = HtmlResponse(url=sub_category_link, body=subCategoryLinkResponse.text,
                                               encoding='utf-8')
        product_list = subCategoryLinkResponse.xpath(
            "//a[@class='grid-product__link']/@href").extract()
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
        # try:
        #     nextPageUrl = subCategoryLinkResponse.xpath(
        #         "//a[@title='Next']/@href").get()
        #     if not nextPageUrl.startswith(store_url):
        #         nextPageUrl = store_url.rstrip('/') + nextPageUrl
        #         print("NEXT PAGE :", nextPageUrl)
        #     self.listing(nextPageUrl, category)
        # except:
        #     pass

    def GetProducts(self, response):
        ignorProduct = self.IgnoreProduct(response)
        if ignorProduct == True:
            self.ProductIsOutofStock(GetterSetter.ProductUrl)
        if re.search('application/ld', response.text):
            productJsonStr = response.xpath(
                "//script[@type='application/ld+json' and contains(text(),'Product')]/text()").get()
            self.product_json= json.loads(productJsonStr)
        categoryAndName = self.GetCategory(response) + " " + self.GetName(response)
        if (re.search(r'\b' + 'new' + r'\b', categoryAndName, re.IGNORECASE)) and not \
                re.search(r'\b((shirt(dress?)|jump(suit?)|dress|gown|romper|suit|caftan)(s|es)?)\b', categoryAndName,
                          re.IGNORECASE):
            print('Skipping Non Dress Product')
            self.ProductIsOutofStock(GetterSetter.ProductUrl)
        else:
            self.GetProductInfo(response)

    def GetName(self, response):
        color = self.GetSelectedColor(response)
        name = self.product_json['name']
        if not color == '' and not re.search(color, name, re.I):
            name = name + " - " + color
        return name

    def GetSelectedColor(self, response):
        color = response.xpath("//div[@data-handle='color']/select//text()").get()
        if color != None:
            return str(color).strip()
        else:
            color = self.product_json['name']
            return color

    def GetPrice(self, response):
        orignalPrice = response.xpath("//span[contains(@class,'price--compare')]/span/text()").get()
        if orignalPrice != None:
            return float(str(orignalPrice).strip().replace('$', '').replace(',', '').replace('USD', ''))
        else:
            regularPrice = self.product_json['offers']['price']
            return float(str(regularPrice).strip().replace('$', '').replace(',', '').replace('USD', ''))

    def GetSalePrice(self, response):
        salePrice = self.product_json['offers']['price']
        if salePrice is not None:
            return float(str(salePrice).strip().replace('$', '').replace(',', '').replace('USD', ''))
        else:
            return 0

    def GetBrand(self, response):
        return self.product_json['brand']['name']

    def GetDescription(self, response):
        return self.product_json['description']

    def GetSizes(self, response):
        sizes = []
        sizeList = response.xpath(
            "///div[contains(@data-handle,'size')]/select/option[@selected='selected']")
        gender = ProductFilters.objects.get(ProductUrl=GetterSetter.ProductUrl).ParentCategory.split(',')[0]
        color = self.GetSelectedColor(response)
        for size in sizeList:
            sizename = size.xpath("./text()").get().strip()
            available = True
            fitType = GetFitType(gender, sizename)
            sizes.append((color, sizename, available, fitType, 0.0, 0.0))
        return sizes
    def GetImageUrl(self, response):
        imageUrls = []
        image_nodes = self.product_json['image']
        for image in image_nodes:
            imageUrls.append(image)
        return imageUrls

    def GetCategory(self, response):
        siteMapCategory = str(Spider_BaseClass.ProductUrlsAndCategory.get(GetterSetter.ProductUrl)).replace('None', '')
        return "Women " + "Men " + siteMapCategory + "jeans "
