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


class HipScrapper(Spider_BaseClass):
    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(HipScrapper, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        return spider

    def GetProductUrls(self, homePageResponse):
        # ========== Category And Subcategory ==========#
        topCategoryNodes = homePageResponse.xpath(
            "//ul[@id='nav-menu']/li[a[text()='Womens']]")
        for topCategoryNode in topCategoryNodes:
            topCategoryTitle = topCategoryNode.xpath("./a/text()").get().strip()
            topCategorylink = topCategoryNode.xpath("./a/@href").get()
            if not topCategorylink.startswith(store_url):
                topCategorylink = store_url.rstrip('/') + topCategorylink
            print("TOP CATEGORY  :", topCategoryTitle, "TOP CATEGORY LINK  :", topCategorylink)
            categoryNodes = topCategoryNode.xpath(
                "./div[contains(@class,'nav-dropdown ')]/div/div[@class='section-list']/ul/li/a[contains(text(),'Dresses')]")
            for categoryNode in categoryNodes:
                categoryTitle = categoryNode.xpath("./text()").get().strip()
                categorylink = categoryNode.xpath("./@href").get()
                if not categorylink.startswith(store_url):
                    categorylink = store_url.rstrip('/') + categorylink
                print("CATEGORY  :", categoryTitle, "CATEGORY LINK  :", categorylink)
                if re.search('\?', categorylink):
                    categorylink = 'https' + categorylink.split('https' or 'http')[1].split('?')[0].strip()

                category = topCategoryTitle + " " + categoryTitle
                self.listing(categorylink, category)
        return Spider_BaseClass.AllProductUrls

    def listing(self, categorylink, category):
        categoryLinkResponse = requests.get(categorylink)
        categoryLinkResponse = HtmlResponse(url=categorylink, body=categoryLinkResponse.text, encoding='utf-8')
        product_list = categoryLinkResponse.xpath(
            "//a[@data-e2e='plp-productList-link']/@href").extract()
        for productUrl in product_list:
            if not productUrl.startswith(store_url):
                productUrl = store_url.rstrip('/') + productUrl
            Spider_BaseClass.AllProductUrls.append(productUrl)
            siteMapCategory = str(Spider_BaseClass.ProductUrlsAndCategory.get(productUrl)).replace('None', '')
            if siteMapCategory:
                Spider_BaseClass.ProductUrlsAndCategory[productUrl] = siteMapCategory + " " + category
            else:
                Spider_BaseClass.ProductUrlsAndCategory[productUrl] = category
        try:
            nextPageUrl = categoryLinkResponse.xpath("//a[@rel='next'][1]/@href").extract()[0]
            print('nextPageUrl:', nextPageUrl)
            if not nextPageUrl.startswith(store_url):
                nextPageUrl = store_url.rstrip('/') + nextPageUrl
            self.listing(nextPageUrl, category)
        except:
            pass

    def GetProducts(self, response):
        global productjson
        responseJson = response.xpath(
            "//script[contains(@type,'application/ld+json') and contains(text(),'Product')]/text()").get()
        productjson = json.loads(responseJson)
        self.GetProductInfo(response)

    def GetName(self, response):
        # color = self.GetSelectedColor(response)
        name = response.xpath("//div[@id='pdp-title-container']/div/h2/text()").get()
        # if not color == '' and not re.search(color, name):
        #     name = name + " - " + color
        return name

    def GetSelectedColor(self, response):
        return productjson['color']

    def GetPrice(self, response):
        orignalPrice = response.xpath(
            "//div[@class='itemPrices']/span[@data-oi-price]/text()").get()
        if orignalPrice != None:
            return float(str(orignalPrice).replace('$', '').replace('£', '').replace('.', ''))
        else:
            regularPrice = response.xpath(
                "//div[@class='itemPrices']/div/span[@class='was']/span/text()").get()
            return float(str(regularPrice).replace('$', '').replace('£', '').replace('.', ''))

    def GetSalePrice(self, response):
        salePrice = response.xpath(
            "//div[@class='itemPrices']/span[@class='now']/span[@data-oi-price]/text()").get()
        if salePrice != None:
            return float(str(salePrice).replace("$", "").replace('£', '').replace('.', ''))
        else:
            return 0

    def GetBrand(self, response):
        return response.xpath("//div[@id='pdp-title-container']/div/h1/text()").get()

    def GetImageUrl(self, response):
        imageUrls = []
        for image in productjson['image']:
            imageUrls.append(image)
        return imageUrls

    def GetDescription(self, response):
        return productjson['description']

    def GetSizes(self, response):
        productSizes = []
        colorName = self.GetSelectedColor(response)
        sizeOptions = response.xpath("//div[@id='sizeOptions']/div/div/button/text()").extract()
        for size in sizeOptions:
            available = True
            sizelist = str(colorName), str(size), available, 0.0, 0.0
            productSizes.append(sizelist)
            break

        return productSizes

    def IgnoreProduct(self, response):
        productAvailability = productjson['offers']['availability']
        if 'InStock' in productAvailability:
            return False
        else:
            return True

    def GetCategory(self, response):
        filterList = []
        if GetterSetter.ProductUrl in Spider_BaseClass.ProductUrlsAndCategory:
            categories = Spider_BaseClass.ProductUrlsAndCategory[GetterSetter.ProductUrl]
            for category in str(categories).split('$'):
                filterList.append(category)
        filters = '$'.join(map(str, filterList))
        return filters
