from BaseClass import *
from scrapy import signals
from WebDriver import SeleniumResponse

DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(DIR.parent.parent.parent.parent))
__package__ = DIR.name

import django

django.setup()

store_url = sys.argv[4]


class FreepeopleScrapper(Spider_BaseClass):
    Spider_BaseClass.cookiesDict = {"currency": "USD", "currencyOverride": "USD"}
    Spider_BaseClass.hasDriver = True

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(FreepeopleScrapper, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        return spider

    def GetProductUrls(self, response):
        category_nodes = response.xpath(
            "//ul[@aria-label='Main Navigation']/li/div/a[contains(text(),'Dresses') or contains(text(),'Clothes') "
            "or contains(text(),'Sale') or contains(text(),'Intimates')]")
        for category_node in category_nodes:
            category_title = category_node.xpath('./text()').get().strip()
            print("Category: ", category_title)
            category_link = category_node.xpath('./@href').get()
            if not category_link.startswith(store_url):
                category_link = store_url + category_link
                print("Link", category_link)
            seleniumResponse = SeleniumResponse(category_link)
            sub_category_nodes = seleniumResponse.xpath(
                "//ul[@class='c-pwa-left-navigation__list']/li//div/a[contains(text(),'Dresses')  or contains(text("
                "),'Jumpsuits') or contains(text(),'loungewear') or contains(text(),'Bodysuits') or contains(text(),"
                "'Clothing') or contains(text(),'Sets') and not(contains(text(),'Underwear'))]")
            for sub_category_node in sub_category_nodes:
                sub_category_title = str(sub_category_node.xpath('./text()').get()).strip()
                sub_category_link = sub_category_node.xpath('./@href').get()
                if not sub_category_link.startswith(store_url):
                    sub_category_link = store_url + sub_category_link
                category = category_title + " " + sub_category_title
                self.listing(sub_category_link, category)
                print(sub_category_title, ":", sub_category_link)
        return Spider_BaseClass.AllProductUrls

    def listing(self, sub_category_link, category):
        seleniumResponse = SeleniumResponse(sub_category_link)
        product_list = seleniumResponse.xpath("//a[contains(@class,'product-tile__link')]/@href").extract()
        for product_url in product_list:
            if not product_url.startswith(store_url):
                product_url = (store_url.rstrip('/') + product_url).split("&type")[0]
            product_url = product_url.split("&type")[0]
            Spider_BaseClass.AllProductUrls.append(product_url)
            siteMapCategory = str(Spider_BaseClass.ProductUrlsAndCategory.get(product_url)).replace('None', '')
            if siteMapCategory:
                Spider_BaseClass.ProductUrlsAndCategory[product_url] = siteMapCategory + " " + category
            else:
                Spider_BaseClass.ProductUrlsAndCategory[product_url] = category
        try:
            next_page_url = seleniumResponse.xpath("//a[@aria-label='Next']/@href").get()
            if not next_page_url.startswith(store_url):
                next_page_url = store_url + next_page_url
            self.listing(next_page_url, category)
        except:
            pass

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
            "//span[contains(@aria-label,'Original price')]/text()").get()
        if orignalPrice != None:
            return float(str(orignalPrice).strip().replace('$', '').replace(',', ''))
        else:
            regularPrice = response.xpath(
                "//span[contains(@aria-label,'Sale price')]/text()").get()
            return float(str(regularPrice).strip().replace('$', '').replace(',', ''))

    def GetSalePrice(self, response):
        salePrice = response.xpath(
            "//span[contains(@aria-label,'Sale price')]/text()").get()
        if salePrice != None:
            return float(str(salePrice).strip().replace('$', '').replace(',', ''))
        else:
            return 0

    def GetBrand(self, response):
        try:
            return str(response.xpath("//a[contains(@class,'product-partner')]/text()").get()).split("all")[1]
        except:
            return "FREEPEOPLE"

    def GetImageUrl(self, response):
        imageUrls = []
        images = response.xpath(
            "//img[contains(@class,'image-viewer_')]/@src").extract()
        for image in images:
            imageUrls.append(image)
        return imageUrls

    def GetDescription(self, response):
        return ' '.join(
            response.xpath("//div[contains(@class,'c-pwa-product-accordions')]/div//text()").extract()).strip()

    def GetSizes(self, response):
        sizes = []
        sizeList = response.xpath(
            "//ul[contains(@class,'list--default')]/li/label[not(contains(@class,'is-disabled'))]")
        gender = ProductFilters.objects.get(ProductUrl=GetterSetter.ProductUrl).ParentCategory.split(',')[0]
        color = self.GetSelectedColor(response)
        for size in sizeList:
            sizename = size.xpath("./text()").get().strip()
            available = True
            fitType = GetFitType(gender, sizename)
            sizes.append((color, sizename, available, fitType, 0.0, 0.0))
        return sizes

    def GetCategory(self, response):
        siteMapCategory = str(Spider_BaseClass.ProductUrlsAndCategory.get(GetterSetter.ProductUrl)).replace('None', '')
        return "Women " + siteMapCategory
