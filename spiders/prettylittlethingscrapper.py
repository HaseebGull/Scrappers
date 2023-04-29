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


class PrettylittlethingScrapper(Spider_BaseClass):
    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(PrettylittlethingScrapper, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        return spider

    def GetProductUrls(self, response):
        topCategoryNodes = response.xpath(
            "(//nav[@class='hidden']/ul/li/div[h3/a[contains(text(),'NEW') or contains(text(),'SALE')  or  contains("
            "text(),'SUMMER') or contains(text(),'FIGURE') or contains(text(),'CLOTHING') or contains(text(),"
            "'DRESSES') or contains(text(),'MOLLY')]])[1]")
        for top_category_node in topCategoryNodes:
            top_category_title = top_category_node.xpath("./h3/a/text()").get().strip()
            print("TOP CATEGORY  :", top_category_title)
            category_nodes = top_category_node.xpath("(./ul/li[h4/a[not(contains(text(),'SHOP')) and not(contains(text("
                                                     "),'Sizes')) and not(contains(text(),'MATERNITY')) and not("
                                                     "contains(text(),'SWIMWEAR')) and not(contains(text(),"
                                                     "'ACCESSORIES')) and not(contains(text(),'SHOES')) and not("
                                                     "contains(text(),'BEAUTY'))]])[1]")
            for category_node in category_nodes:
                category_title = category_node.xpath("./h4/a/text()").get().strip()
                print("category_title :", category_title)
                sub_category_nodes = category_node.xpath(
                    "(./ul/li/a[not(contains(text(),'All')) and  contains(text(),'Dresses') or contains(text(),"
                    "'Bodysuits') or contains(text(),'Jump') or contains(text(),'Loungewear') or contains(text(),"
                    "'Petite') or contains(text(),'Skirts')])[1]")
                for sub_category_node in sub_category_nodes:
                    sub_category_title = sub_category_node.xpath("./text()").get().strip()
                    sub_category_link = sub_category_node.xpath("./@href").get()
                    if not sub_category_link.startswith(store_url):
                        sub_category_link = store_url.rstrip('/') + sub_category_link
                    print(sub_category_title, " :", sub_category_link)
                    category = top_category_title + " " + category_title + " " + sub_category_title
                    self.listing(sub_category_link, category)
        return Spider_BaseClass.AllProductUrls

    def listing(self, subCategorylink, category):
        subCategoryLinkResponse = requests.get(subCategorylink)
        subCategoryLinkResponse = HtmlResponse(url=subCategorylink, body=subCategoryLinkResponse.text,
                                               encoding='utf-8')
        product_list = subCategoryLinkResponse.xpath(
            "(//a[contains(@class,'product-url')]/@href)[1]").extract()
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
            nextPageUrl = subCategoryLinkResponse.xpath("//a[@class='load-more-btn']/@href").get()
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
        name = str(response.xpath("//h1[@class='product-view-title']/text()").get()).strip()
        if not color == '' and not re.search(color, name, re.I):
            name = name + " - " + color
        print("name =", name)
        return name

    def GetSelectedColor(self, response):
        color = str(response.xpath("//div[@class='colour-option-label']/p/span[2]/text()").get()).strip()
        return color
    def GetPrice(self, response):
        orignalPrice = response.xpath(
            "//div[contains(@class,'price-target')]/p[contains(@class,'regular')]/span/text()").get()
        if orignalPrice != None:
            return float(str(orignalPrice).strip().replace('$', '').replace(',', '').replace('USD',''))
        else:
            regularPrice = response.xpath(
                "//div[contains(@class,'price-target')]/p[contains(@class,'old')]/span/text()").get()
            return float(str(regularPrice).strip().replace('$', '').replace(',', '').replace('USD',''))

    def GetSalePrice(self, response):
        salePrice = response.xpath(
            "//div[contains(@class,'price-target')]/p[contains(@class,'new')]/span[1]/text()").get()
        if salePrice is not None:
            return float(str(salePrice).strip().replace('$', '').replace(',', '').replace('USD',''))
        else:
            return 0
    def GetDescription(self, response):
        return ' '.join(response.xpath("//div[contains(@class,'description')]//p//text()").extract()).strip()

    def GetBrand(self, response):
        brand = str(response.text).split("brand':")[1].split(',')[0].replace('"',"")
        return brand
    def GetSizes(self, response):
        sizes = []
        sizeList = response.xpath(
            "//div[contains(@class,'size-in-stock')]")
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
            "//div[@itemprop='associatedMedia']/img")
        for image in image_nodes:
            umage_url = image.xpath("./@src").get().strip()
            imageUrls.append(umage_url)
        return imageUrls
    def GetCategory(self, response):
        siteMapCategory = str(Spider_BaseClass.ProductUrlsAndCategory.get(GetterSetter.ProductUrl)).replace('None', '')
        return "Women " + siteMapCategory +  "jeans "