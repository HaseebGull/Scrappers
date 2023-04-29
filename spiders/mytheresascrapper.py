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


class MytheresaScrapper(Spider_BaseClass):
    Spider_BaseClass.hasDriver = True

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(MytheresaScrapper, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        return spider

    def GetProductUrls(self, response):
        gender_nodes = response.xpath(
            "//ul[@class='meta-list-department']/li/a[not(contains(text(),'LIFE'))]")
        for gender_node in gender_nodes:
            gender_title = gender_node.xpath("./text()").get().strip()
            print(gender_title)
        top_category_nodes = response.xpath(
            "//li[contains(@class,'level0')][a/span[contains(text(),'New Arrivals') or contains(text(),"
            "'Clothing') or contains(text(),'Girls') or contains(text(),'Boys') or contains(text(),'Sale')]]")
        for top_category_node in top_category_nodes:
            top_category_link = top_category_node.xpath("./a/@href").get()
            top_category_title = top_category_node.xpath("./a/span/text()").get().strip()
            print("cat_title :", top_category_title, " :", top_category_link)
            category_nodes = top_category_node.xpath("./div[contains(@class,'menu-flyout')]//ul[li[contains(text(),'Just in') or contains(text(),'Shop by category') or contains(text(),'JUST IN')]]")
            for category_node in category_nodes:
                category_title = category_node.xpath('./li/text()').get().strip()
                print("Category: ", category_title)
                # if str(gender_title).lower() in category_link:
                sub_category_nodes = category_node.xpath(
                    "./li[a/span[contains(text(),'Dresses') or contains(text(),'Jumpsuits') or contains(text(),'Bridal Clothes') or contains(text(),'Clothing') or contains(text(),'dresses') or contains(text(),'kaftans') or contains(text(),'jumpsuits')]]")
                for sub_category_node in sub_category_nodes:
                    sub_category_title = sub_category_node.xpath("./a/span/text()").get().strip()
                    sub_category_link = sub_category_node.xpath("./a/@href").get()
                    if not sub_category_link.startswith(store_url):
                        sub_category_link = store_url + sub_category_link
                    print("sub_category_link  :", sub_category_link)
                    category = "Women" + "Men" + "Girl" + "boy"
                    self.listing(sub_category_link, category)
        return Spider_BaseClass.AllProductUrls

    def listing(self, subCategorylink, category):
        # subCategoryLinkResponse = requests.get(subCategorylink)
        # subCategoryLinkResponse = HtmlResponse(url=subCategorylink, body=subCategoryLinkResponse.text,
        #                                        encoding='utf-8')
        subCategoryLinkResponse = SeleniumResponse(subCategorylink)
        product_list = subCategoryLinkResponse.xpath(
            "//div[@class='product-info']/h2/a/@href").extract()
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
        try:
            nextPageUrl = subCategoryLinkResponse.xpath("//li[@class='next']/a/@href").get()
            if not nextPageUrl.startswith(store_url):
                nextPageUrl = store_url.rstrip('/') + nextPageUrl
                print("NEXT PAGE :", nextPageUrl)
            self.listing(nextPageUrl, category)
        except:
            pass

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
        name = str(response.xpath("//div[@class='product-name']/span/text()").get()).strip()
        if not color == '' and not re.search(color, name, re.I):
            name = name + " - " + color
        print("name =", name)
        return name

    def GetSelectedColor(self, response):
        return "color"

    def GetPrice(self, response):
        orignalPrice = response.xpath(
            "//div[@class='product-shop']//span[@class='regular-price']/span/text()").get()
        if orignalPrice != None:
            return float(str(orignalPrice).strip().replace('$', '').replace(',', '').replace('USD', ''))
        else:
            regularPrice = response.xpath(
                "//span[contains(@id,'old-price')]/text()").get()
            return float(str(regularPrice).strip().replace('$', '').replace(',', '').replace('USD', ''))

    def GetSalePrice(self, response):
        salePrice = response.xpath(
            "//div[@class='price-info ']//p[@class='special-price']/span/text()").get()
        if salePrice is not None:
            return float(str(salePrice).strip().replace('$', '').replace(',', '').replace('USD', ''))
        else:
            return 0

    def GetBrand(self, response):
        return str(response.xpath("//div[@class='product-designer']/h2/a/text()").get()).strip()

    def GetDescription(self, response):
        des = response.xpath(
            "//div[contains(@class,'product-collateral')]//div/p[contains(@class,'product-description')]/text()").get().strip()
        des2 = ' '.join(response.xpath(
            "//div[contains(@class,'product-collateral')]//div/ul[contains(@class,'featurepoints')]/li/text()").extract()).strip()
        return des + des2

    def GetSizes(self, response):
        sizes = []
        sizeList = response.xpath(
            "//ul[@class='sizes']/li/a[not(contains(text(),'Add'))]")
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
        image_nodes = response.xpath(
            "//div[@class='product-image-gallery']/div/img")
        for image in image_nodes:
            umage_url = image.xpath("./@src").get()
            imageUrls.append(umage_url)
        return imageUrls

    def GetCategory(self, response):
        siteMapCategory = str(Spider_BaseClass.ProductUrlsAndCategory.get(GetterSetter.ProductUrl)).replace('None', '')
        return "Women " + " Men " + "Girls " + "Boys " + siteMapCategory
