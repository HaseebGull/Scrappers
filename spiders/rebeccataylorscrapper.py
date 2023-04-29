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


class RebeccaTaylorScrapper(Spider_BaseClass):
    Spider_BaseClass.cookiesDict = {
        "GlobalE_Data": "%7B%22countryISO%22%3A%22US%22%2C%22cultureCode%22%3A%22en-GB%22%2C%22currencyCode%22%3A%22USD%22%2C%22apiVersion%22%3A%222.1.4%22%2C%22clientSettings%22%3A%22%7B%5C%22AllowClientTracking%5C%22%3A%7B%5C%22Value%5C%22%3A%5C%22true%5C%22%7D%2C%5C%22CDNEnabled%5C%22%3A%7B%5C%22Value%5C%22%3A%5C%22true%5C%22%7D%2C%5C%22CheckoutContainerSuffix%5C%22%3A%7B%5C%22Value%5C%22%3A%5C%22Global-e_International_Checkout%5C%22%7D%2C%5C%22FullClientTracking%5C%22%3A%7B%5C%22Value%5C%22%3A%5C%22true%5C%22%7D%2C%5C%22IsMonitoringMerchant%5C%22%3A%7B%5C%22Value%5C%22%3A%5C%22true%5C%22%7D%2C%5C%22IsV2Checkout%5C%22%3A%7B%5C%22Value%5C%22%3A%5C%22true%5C%22%7D%2C%5C%22SetGEInCheckoutContainer%5C%22%3A%7B%5C%22Value%5C%22%3A%5C%22true%5C%22%7D%2C%5C%22AdScaleClientSDKURL%5C%22%3A%7B%5C%22Value%5C%22%3A%5C%22https%3A%2F%2Fweb.global-e.com%2Fmerchant%2FGetAdScaleClientScript%3FmerchantId%3D460%5C%22%7D%2C%5C%22AmazonUICulture%5C%22%3A%7B%5C%22Value%5C%22%3A%5C%22en-GB%5C%22%7D%2C%5C%22AnalyticsUrl%5C%22%3A%7B%5C%22Value%5C%22%3A%5C%22https%3A%2F%2Fservices.global-e.com%2F%5C%22%7D%2C%5C%22CDNUrl%5C%22%3A%7B%5C%22Value%5C%22%3A%5C%22https%3A%2F%2Fwebservices.global-e.com%2F%5C%22%7D%2C%5C%22ChargeMerchantForPrepaidRMAOfReplacement%5C%22%3A%7B%5C%22Value%5C%22%3A%5C%22false%5C%22%7D%2C%5C%22CheckoutCDNURL%5C%22%3A%7B%5C%22Value%5C%22%3A%5C%22https%3A%2F%2Fwebservices.global-e.com%2F%5C%22%7D%2C%5C%22EnableReplaceUnsupportedCharactersInCheckout%5C%22%3A%7B%5C%22Value%5C%22%3A%5C%22false%5C%22%7D%2C%5C%22GTM_ID%5C%22%3A%7B%5C%22Value%5C%22%3A%5C%22GTM-PWW94X2%5C%22%7D%2C%5C%22InternalTrackingEnabled%5C%22%3A%7B%5C%22Value%5C%22%3A%5C%22false%5C%22%7D%2C%5C%22PixelAddress%5C%22%3A%7B%5C%22Value%5C%22%3A%5C%22https%3A%2F%2Futils.global-e.com%5C%22%7D%2C%5C%22RefundRMAReplacementShippingTypes%5C%22%3A%7B%5C%22Value%5C%22%3A%5C%22%5B2%2C3%2C4%5D%5C%22%7D%2C%5C%22RefundRMAReplacementStatuses%5C%22%3A%7B%5C%22Value%5C%22%3A%5C%22%5B9%2C11%2C12%5D%5C%22%7D%2C%5C%22TrackingV2%5C%22%3A%7B%5C%22Value%5C%22%3A%5C%22true%5C%22%7D%2C%5C%22MerchantIdHashed%5C%22%3A%7B%5C%22Value%5C%22%3A%5C%22mZ4H%5C%22%7D%7D%22%7D;"}

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(RebeccaTaylorScrapper, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        return spider

    def GetProductUrls(self, homePageResponse):
        # ========== Category And Subcategory ==========#
        topCategoryNodes = homePageResponse.xpath(
            "//ul[contains(@class,'menu-category')]/li[a[not(contains(text(),'Our Stores'))]]")
        for topCategoryNode in topCategoryNodes:
            topCategoryTitle = topCategoryNode.xpath("./a/text()").get().strip()
            if not 'Women' in topCategoryTitle:
                topCategoryTitle = "Women " + topCategoryTitle
            topCategorylink = topCategoryNode.xpath("./a/@href").get()
            if not topCategorylink.startswith(store_url):
                topCategorylink = store_url.rstrip('/') + topCategorylink
            if 'Shop All' in topCategoryTitle:
                categoryNodes = topCategoryNode.xpath(
                    "./div//ul/li[a]/ul/li/a[contains(text(),'Dress')]")
            else:
                categoryNodes = topCategoryNode.xpath(
                    "./div[@class='level-2']/div/ul/li/a[not(contains(text(),'All')) and contains(text(),'Dress') "
                    "or contains(text(),'Print') "
                    "or contains(text(),'Essentials') or contains(text(),'Escape') or contains(text(),'Edit')]")
            if not categoryNodes:
                category = topCategoryTitle
                self.listing(topCategorylink, category)
            else:
                for categoryNode in categoryNodes:
                    categoryTitle = categoryNode.xpath("./text()").get().strip()
                    categorylink = categoryNode.xpath("./@href").get()
                    if not categorylink.startswith(store_url):
                        categorylink = store_url.rstrip('/') + categorylink
                    category = topCategoryTitle + " " + categoryTitle
                    self.listing(categorylink, category)
        return Spider_BaseClass.AllProductUrls

    def listing(self, categorylink, category):
        categoryLinkResponse = requests.get(categorylink, stream=True)
        categoryLinkResponse = HtmlResponse(url=categorylink, body=categoryLinkResponse.text, encoding='utf-8')
        product_list = categoryLinkResponse.xpath(
            "//a[@class='name-link']/@href").extract()
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
                "//div[contains(@class,'infinite-scroll')]/@data-grid-url").get()
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
            self.GetProductInfo(response)

    def GetProducts(self, response):
        global productjson
        ignorProduct = self.IgnoreProduct(response)
        if ignorProduct == True:
            self.ProductIsOutofStock(GetterSetter.ProductUrl)
        else:
            categoryAndName = self.GetCategory(response) + " " + self.GetName(response)
            if (re.search('New', categoryAndName, re.IGNORECASE) or re.search('Edits', categoryAndName,
                                                                              re.IGNORECASE)) and not re.search(
                    r'\b((shirt(dress?)|jump(suit?)|dress|gown|set|romper|suit|caftan)(s|es)?)\b', categoryAndName,
                    re.IGNORECASE):
                print('Skipping Non Dress Product')
                self.ProductIsOutofStock(GetterSetter.ProductUrl)
            else:
                self.GetProductInfo(response)

    def IgnoreProduct(self, response):
        availability = response.xpath("//div[@class='price-holder']/div/meta[@itemprop='availability']/@content").get()
        if not 'InStock' in availability:
            return True
        else:
            return False

    def GetName(self, response):
        color = self.GetSelectedColor(response)
        name = response.xpath("//h1[@class='product-name']/text()").get()
        if not color == '' and not re.search(color, name):
            name = name + " - " + color
        return name

    def GetSelectedColor(self, response):
        colorID = ''
        images = response.xpath("//div[contains(@class,'product-vertical')]/div/a/@href").get()
        if re.search('/large/', str(images)):
            colorID = str(images).split('/large/')[1].split('.jpg')[
                0].strip().rstrip('.jpg')
        colorName = response.xpath(
            "//ul[@class='swatches color']/li/a[contains(@data-lgimg,'" + colorID + "')]/img/@alt").get()
        return colorName

    def GetPrice(self, response):
        orignalPrice = response.xpath("//div[@class='product-price']/span[@class='price-sales ']/text()").get()
        if orignalPrice != None:
            return float(str(orignalPrice).replace('$', '').replace(',', ''))
        else:
            regularPrice = response.xpath(
                "//div[@class='product-price']/span[@class='price-standard']/text()").get()
            return float(str(regularPrice).replace('$', '').replace(',', ''))

    def GetSalePrice(self, response):
        salePrice = response.xpath(
            "//div[@class='product-price']/span[contains(@class,'markeddown-price')]/text()").get()
        if salePrice != None:
            return float(str(salePrice).replace("$", "").replace(',', ''))
        else:
            return 0

    def GetBrand(self, response):
        return 'Rebecca Taylor'

    def GetImageUrl(self, response):
        imageUrls = []
        images = response.xpath("//div[contains(@class,'product-vertical')]/div/a/@href").extract()
        for image in images:
            imageUrls.append(image)
        return imageUrls

    def GetDescription(self, response):
        detial = response.xpath("//div[contains(@class,'pdp-detail-para')]/p").get()
        detailList = ' '.join(
            response.xpath("//div[contains(@class,'pdp-detail-para')]/ul/li/text()").extract()).replace('\n', '')
        return str(detial) + " " + str(detailList)

    def GetSizes(self, response):
        productSizes = []
        colorName = self.GetSelectedColor(response)
        gender = ProductFilters.objects.get(ProductUrl=GetterSetter.ProductUrl).ParentCategory.split(',')[0]
        sizeOptions = response.xpath(
            "//div[@id='product-content']//div[@class='product-variations']//ul[contains(@class,'swatches size')]/li[contains(@class,'selectable')]/a")
        for sizeOption in sizeOptions:
            sizeName = sizeOption.xpath("./text()").get().strip()
            fitType = GetFitType(gender, str(sizeName).strip())
            available = True
            sizelist = str(colorName), str(sizeName), available, str(fitType), 0.0, 0.0
            productSizes.append(sizelist)
        return productSizes

    def GetCategory(self, response):
        filterList = []
        global categoryjson
        siteMapCategory = str(Spider_BaseClass.ProductUrlsAndCategory.get(GetterSetter.ProductUrl)).replace('None', '')

        if re.search('dataLayer = \[', response.text):
            categoryjson = response.text.split('dataLayer = [')[1].split('];')[0].strip()
            categoryjson = json.loads(categoryjson)

        categories = categoryjson['ecommerce']['detail']['products']
        for category in categories:
            categoryName = category['category']
            filterList.append(categoryName)

        filters = ' '.join(map(str, filterList))
        return siteMapCategory + " " + filters
