import sys
from pathlib import Path

DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(DIR.parent.parent.parent.parent))
__package__ = DIR.name

import django

django.setup()
from BaseClass import *
from scrapy import signals
from Magento import magento

store_url = sys.argv[4]


class ForcastScraper(magento):
    # Spider_BaseClass.cookies_dict = {"Cookie": "currency=USD&form_key=aDfg6JUDzadNVVru"}
    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(ForcastScraper, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        return spider

    def GetProductUrls(self, homePageResponse):
        # ========== Category And Subcategory ==========#

        topCategoryNodes = homePageResponse.xpath(
            "//nav[@class='navigation']/ul/li[a[contains(span/text(),'CLOTHING') or contains(span/text(),'WORKWEAR') or contains(span/text(),'SALE')]]")
        for topCategoryNode in topCategoryNodes:
            topCategoryTitle = topCategoryNode.xpath("./a/span/text()").get().strip()
            topCategorylink = topCategoryNode.xpath("./a/@href").get()
            if not topCategorylink.startswith(store_url):
                topCategorylink = store_url.rstrip('/') + topCategorylink
            print("TOP CATEGORY  :", topCategoryTitle, ": TOP CATEGORY LINK  :", topCategorylink)

            categoryNodes = topCategoryNode.xpath(
                "./ul/li/div/div/ul/li[a[contains(span/text(),'Dress') or contains(span/text(),'Jumpsuits') or contains(span/text(),'Knitwear') or contains(span/text(),'Clothing')]]")
            for categoryNode in categoryNodes:
                categoryTitle = categoryNode.xpath("./a/span/text()").get().strip()
                categorylink = categoryNode.xpath("./a/@href").get()
                if not categorylink.startswith(store_url):
                    categorylink = store_url.rstrip('/') + categorylink
                print("CATEGORY  :", categoryTitle, ": CATEGORY LINK  :", categorylink)
                if re.search('\?', categorylink):
                    categorylink = 'https' + categorylink.split('https' or 'http')[1].split('?')[0].strip()

                subCategoryNodes = categoryNode.xpath(
                    "./ul/li/a[contains(span/text(),'Dress') or contains(span/text(),'Jumpsuits')]")
                if subCategoryNodes:
                    for subCategoryNode in subCategoryNodes:
                        subCategoryTitle = subCategoryNode.xpath("./span/text()").get().strip()
                        subCategorylink = subCategoryNode.xpath("./@href").get()
                        if not subCategorylink.startswith(store_url):
                            subCategorylink = store_url.rstrip('/') + subCategorylink
                        print("SUB CATEGORY  :", subCategoryTitle, ":  SUB CATEGORY LINK  :", subCategorylink)
                        if re.search('\?', subCategorylink):
                            subCategorylink = 'https' + subCategorylink.split('https' or 'http')[1].split('?')[
                                0].strip()

                        category = topCategoryTitle + " " + categoryTitle + " " + subCategoryTitle
                        print("BreadCrum : ", category)
                        self.listing(subCategorylink, category)
                else:
                    self.listing(categorylink, categoryTitle)

        return Spider_BaseClass.AllProductUrls

    def listing(self, categorylink, category):
        categoryLinkResponse = requests.get(categorylink, stream=True)
        categoryLinkResponse = HtmlResponse(url=categorylink, body=categoryLinkResponse.text, encoding='utf-8')
        product_list = categoryLinkResponse.xpath(
            "//a[contains(@class,'product-item-photo')]/@href").extract()
        for productUrl in product_list:
            if not productUrl.startswith(store_url):
                productUrl = store_url.rstrip('/') + productUrl
            if re.search('https://', productUrl) and re.search('.html', productUrl):
                productUrl = 'https://' + productUrl.split('https://')[1].split('.html')[0].strip() + '.html'
            print("Product URL  :", productUrl)
            Spider_BaseClass.AllProductUrls.append(productUrl)
            siteMapCategory = str(Spider_BaseClass.ProductUrlsAndCategory.get(productUrl)).replace('None', '')
            if siteMapCategory:
                Spider_BaseClass.ProductUrlsAndCategory[productUrl] = siteMapCategory + " " + category
            else:
                Spider_BaseClass.ProductUrlsAndCategory[productUrl] = category
        try:
            pass
            nextPageUrl = categoryLinkResponse.xpath(
                "(//a[contains(@class,'next')]/@href)[1]").get()
            print('nextPageUrl:', nextPageUrl)
            if not nextPageUrl.startswith(store_url):
                nextPageUrl = store_url.rstrip('/') + nextPageUrl
            self.listing(nextPageUrl, category)
        except:
            pass

    def SetProductJson(self, response):
        if re.search('"jsonConfig":', response):
            return str(response.split('"jsonConfig": ')[1].split('"jsonSwatchConfig":')[0]).strip().rstrip(',')
        return ''

    def GetName(self, response):
        color = self.GetSelectedColor(response)
        name = response.xpath("//span[@itemprop='name']/text()").get()
        # if not color == '' and not re.search(color, name, re.I):
        #     name = name + " - " + color
        return name

    def GetSelectedColor(self, response):
        color = response.xpath(
            "//div[contains(@class,'watch-attribute') and contains(@attribute-code,'color')]/span[contains(@class,'selected')]").get()
        print(color)
        return color

    # def IgnoreProduct(self, response):
    #     if re.search('"availability":"', response.text):
    #         productAvailability = response.text.split('"availability":"')[1].split('"}}')[0].strip()
    #         if not 'InStock' in productAvailability or 'PreOrder' in productAvailability:
    #             return True
    #         else:
    #             return False
    #
    def GetDescription(self, response):
        return ','.join(response.xpath(
            "//div[contains(@class,'description')]/div[@class='value']//div[@data-content-type='text']/p/text()").extract())

    def GetCategory(self, response):
        filterList = []
        if GetterSetter.ProductUrl in Spider_BaseClass.ProductUrlsAndCategory:
            categories = Spider_BaseClass.ProductUrlsAndCategory[GetterSetter.ProductUrl]
            for category in str(categories).split('$'):
                filterList.append(category)
        filters = '$'.join(map(str, filterList))
        return 'Women ' + filters
