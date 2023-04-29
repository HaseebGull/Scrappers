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


class ReformationScrapper(Spider_BaseClass):
    Spider_BaseClass.cookiesDict = {
        "GlobalE_Data": "%7B%22countryISO%22%3A%22US%22%2C%22cultureCode%22%3A%22en-GB%22%2C%22currencyCode%22%3A%22USD%22%2C%22apiVersion%22%3A%222.1.4%22%7D; "}

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(ReformationScrapper, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        return spider

    def GetProductUrls(self, homePageResponse):
        gender = 'Women'
        # ========== Category And Subcategory ==========#
        topCategoryNodes = homePageResponse.xpath(
            "//ul[@role='menu']/li[a[contains(text(),'Clothing') or contains(text(),'Dresses') or contains(text(),'Weddings') or contains(text(),'New') or contains(text(),'Active') ]]")
        for topCategoryNode in topCategoryNodes:
            topCategoryTitle = topCategoryNode.xpath("./a/text()").get().strip()
            topCategorylink = topCategoryNode.xpath("./a/@href").get()
            if not topCategorylink.startswith(store_url):
                topCategorylink = store_url.rstrip('/') + topCategorylink

            categoryNodes = topCategoryNode.xpath(
                ".//div/ul/li/ul/li/a[not(contains(text(),'All')) and contains(text(),'Dresses') or contains(text(),'dress') or contains(text(),'Bodysuits') or contains(text(),'Jumpsuits') or contains(text(),'Two Piece Sets')]")
            for categoryNode in categoryNodes:
                categoryTitle = categoryNode.xpath("./text()").get().strip()
                categorylink = categoryNode.xpath("./@href").get()
                if not categorylink.startswith(store_url):
                    categorylink = store_url.rstrip('/') + categorylink
                category = gender + " " + topCategoryTitle + " " + categoryTitle
                self.listing(categorylink, category)
        return Spider_BaseClass.AllProductUrls

    def listing(self, categorylink, category):
        categoryLinkResponse = requests.get(categorylink, stream=True)
        categoryLinkResponse = HtmlResponse(url=categorylink, body=categoryLinkResponse.text, encoding='utf-8')
        product_list = categoryLinkResponse.xpath(
            "//div[@class='product']/div/a/@href").extract()
        for productUrl in product_list:
            if not productUrl.startswith(store_url):
                productUrl = store_url.rstrip('/') + productUrl
            if re.search('https://', productUrl) and re.search('.html', productUrl):
                productUrl = 'https://' + productUrl.split('https://')[1].split('.html')[0].strip() + '.html'
            Spider_BaseClass.AllProductUrls.append(productUrl)
            siteMapCategory = str(Spider_BaseClass.ProductUrlsAndCategory.get(productUrl)).replace('None', '')
            if siteMapCategory:
                Spider_BaseClass.ProductUrlsAndCategory[productUrl] = siteMapCategory + " " + category
            else:
                Spider_BaseClass.ProductUrlsAndCategory[productUrl] = category
        try:
            pass
            nextPageUrl = categoryLinkResponse.xpath(
                "//button[contains(@data-search-component,'more-products')]/@data-url").get()
            if not nextPageUrl.startswith(store_url):
                nextPageUrl = store_url.rstrip('/') + nextPageUrl
            self.listing(nextPageUrl, category)
        except:
            pass

    def GetProducts(self, response):
        global productjson
        ignorProduct = self.IgnoreProduct(response)
        if ignorProduct == True:
            self.ProductIsOutofStock(GetterSetter.ProductUrl)
        else:
            responseJson = response.xpath("//script[@type='application/ld+json']/text()").get()
            productjson = json.loads(responseJson)
            self.GetProductInfo(response)

    def IgnoreProduct(self, response):
        if re.search('"availability":"', response.text):
            productAvailability = response.text.split('"availability":"')[1].split('"}}')[0].strip()
            if not 'InStock' in productAvailability or 'PreOrder' in productAvailability:
                return True
            else:
                return False

    def GetName(self, response):
        color = self.GetSelectedColor(response)
        name = response.xpath("//h1[@data-product-component='name']/text()").get()
        if not color == '' and not re.search(color, name):
            name = name + " - " + color
        return name

    def GetSelectedColor(self, response):

        color = response.xpath(
            "//label[contains(span/text(),'Color')]/span[contains(@class,'selected-value')]/text()").get()
        if color:
            return color
        else:
            return ''

    def GetPrice(self, response):
        orignalPrice = response.xpath(
            "//div[@class='pdp__content']"
            "//div[@class='price']/span[contains(@class,'price__sales')]/span/span[@class='price--reduced']/text()").get()
        if orignalPrice != None:
            return float(str(orignalPrice).replace('$', '').replace(',', ''))
        else:
            regularPrice = response.xpath(
                "//span[@class='sales']/span/text()").get()
            return float(str(regularPrice).replace('$', '').replace(',', ''))

    def GetSalePrice(self, response):
        salePrice = response.xpath(
            "//div[@class='pdp__content']"
            "//div[@class='price']/span[contains(@class,'price__sales')]/span/span[@class='price--reduced']/text()").get()
        if salePrice != None:
            return float(str(salePrice).replace("$", "").replace(',', ''))
        else:
            return 0

    def GetBrand(self, response):
        return productjson['brand']['name']

    def GetImageUrl(self, response):
        productID = ''
        imageUrls = []
        if re.search('"id":', response.text):
            productID = response.text.split('"id":')[1].split(',')[0].strip().replace('"', '')
        colorId = response.xpath(
            "//button[contains(@class,'product-attribute__swatch') and contains(@class,'selected')]/@data-attr-value").get()
        try:
            imageReq = 'https://res.cloudinary.com/reformation/image/list/' + productID + '-' + colorId + '.json'
        except:
            imageReq = 'https://res.cloudinary.com/reformation/image/list/' + productID + '.json'

        resp = requests.get(imageReq)
        imageJson = json.loads(resp.text)
        for image in imageJson['resources']:
            image = 'https://res.cloudinary.com/reformation/image/upload/b_rgb:FFFFFF,c_limit,dpr_1.0,f_auto,h_673,q_auto,w_1400/c_limit,h_673,w_1400/v1/' + \
                    image['public_id'] + '?pgw=1'
            imageUrls.append(image)
        return imageUrls

    def GetDescription(self, response):
        summary = productjson['description']
        detial = ' '.join(
            response.xpath("//div[contains(@class,'pdp__accordion')]/div/div/ul/li/text()").extract()).replace('\n', '')
        fabric = ' '.join(
            response.xpath("//div[contains(@class,'pdp__accordion')]/div/div/div/text()").extract()).replace('\n', '')

        return str(summary) + " " + str(detial) + " " + str(fabric)

    def GetSizes(self, response):
        productSizes = []
        gender = ProductFilters.objects.get(ProductUrl=GetterSetter.ProductUrl).ParentCategory.split(',')[0]
        colorName = self.GetSelectedColor(response)
        sizeOptions = response.xpath(
            "//div[contains(@class,'product-attribute--size')]/div[contains(@class,'product-attribute__contents')]/button[contains(@class,'selectable') and not(contains(@class,'unselectable'))]/text()").extract()
        for sizeName in sizeOptions:
            fitType = GetFitType(gender, str(sizeName).strip())
            available = True
            sizelist = str(colorName), str(sizeName).strip(), available, str(fitType), 0.0, 0.0
            productSizes.append(sizelist)
        return productSizes

    def GetCategory(self, response):
        siteMapCategory = str(Spider_BaseClass.ProductUrlsAndCategory.get(GetterSetter.ProductUrl)).replace('None', '')
        return siteMapCategory
