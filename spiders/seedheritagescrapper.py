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


class SeedheritageScrapper(Spider_BaseClass):
    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(SeedheritageScrapper, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        return spider

    def GetProductUrls(self, response):
        topCategoryNodes = response.xpath(
            "//div[@id='navigation']//ul[contains(@class,'menu-category')]/li[a[not(contains(text(),'Home')) and not("
            "contains(text(),'Newborn'))]]")
        for top_category_node in topCategoryNodes:
            top_category_title = top_category_node.xpath("./a/text()").get().strip()
            print("TOP CATEGORY  :", top_category_title)
            category_nodes = top_category_node.xpath(
                ".//div[@class='mega-menu-tiles-item'] | .//ul[@class='menu-container-level-2']/li[a[contains(text(),'Clothing')or contains(text(),'Woman') or contains(text(),'Child') or contains(text(),'Baby') or contains(text(),'Girl')]] | .//ul[contains(@class,'menu-container-column')]/li[a]")
            for category_node in category_nodes:
                category_title = category_node.xpath(
                    "./a/text() | ./a/span[not(contains(text(),'Home'))]/text()").get().strip()
                print("category_title :", category_title)
                sub_category_nodes = category_node.xpath(
                    ".//a[span[not(contains(text(),'Home'))]] | .//div[contains(@class,"
                    "'menu-container-level-3')]/ul/li/a[contains(text(),'Dresses') or contains(text(),'Knitwear') or "
                    "contains(text(),'Sleepwear') or contains(text(),'Clothing')] | .//div[contains(@class,"
                    "'menu-container-level-4')]/ul/li/a[contains(text(),'Dresses') or contains(text(),'Knitwear') or "
                    "contains(text(),'Sleepwear') or contains(text(),'Play')]")
                for sub_category_node in sub_category_nodes:
                    sub_category_title = sub_category_node.xpath("./text() | ./span/text()").get().strip()
                    sub_category_link = sub_category_node.xpath("./@href | ./a/@href").get()
                    if not sub_category_link.startswith(store_url):
                        sub_category_link = store_url.rstrip('/') + sub_category_link
                    print(sub_category_title, " :", sub_category_link)
                    category = top_category_title + " " + category_title + " " + sub_category_title
                    self.listing(sub_category_link, category)
        return Spider_BaseClass.AllProductUrls

    def listing(self, subCategorylink, category):
        subCategoryLinkResponse = SeleniumResponse(subCategorylink)
        product_list = subCategoryLinkResponse.xpath("//a[@class='name-link']/@href").extract()
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
            nextPageUrl = subCategoryLinkResponse.xpath("//div[contains(@class,'scroll')]/a/@href").get()
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
        name = str(response.xpath("//h1[@class='product-name ']/text()").get()).strip()
        if not color == '' and not re.search(color, name, re.I):
            name = name + " - " + color
        print("name =", name)
        return name

    def GetSelectedColor(self, response):
        color = str(response.xpath("//span[contains(@class,'color-name')]/text()").get()).strip()
        return color

    def GetPrice(self, response):
        orignalPrice = response.xpath(
            "//div[@class='upper-product-price']//span[contains(@class,'price-standard')]/text()").get()
        if orignalPrice != None:
            return float(str(orignalPrice).strip().replace('$', '').replace(',', '').replace('USD', ''))
        else:
            regularPrice = response.xpath(
                "//div[@class='upper-product-price']//span[contains(@class,'price-sales')]/text()").get()
            return float(str(regularPrice).strip().replace('$', '').replace(',', '').replace('USD', ''))

    def GetSalePrice(self, response):
        salePrice = response.xpath(
            "//div[@class='upper-product-price']//span[contains(@class,'price-sales')]/text()").get()
        if salePrice is not None:
            return float(str(salePrice).strip().replace('$', '').replace(',', '').replace('USD', ''))
        else:
            return 0

    def GetDescription(self, response):
        return ' '.join(
            response.xpath("//div[contains(@class,'product-details-description')]//div//text()").extract()).strip()

    def GetBrand(self, response):
        return "Seed Heritage"

    def GetSizes(self, response):
        sizes = []
        sizeList = response.xpath(
            "//div[@class='product-name-price-container']/following-sibling::div[1]//ul[contains(@class,'size')]/li["
            "not(contains(@class,'unselectable'))]/a")
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
            "//div[@class='image-item-inner']//img")
        for image in image_nodes:
            umage_url = image.xpath("./@src").get()
            imageUrls.append(umage_url)
        return imageUrls

    def GetCategory(self, response):
        siteMapCategory = str(Spider_BaseClass.ProductUrlsAndCategory.get(GetterSetter.ProductUrl)).replace('None', '')
        return "Women " + siteMapCategory
