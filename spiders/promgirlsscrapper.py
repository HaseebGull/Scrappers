import sys
from pathlib import Path
DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(DIR.parent.parent.parent.parent))
__package__ = DIR.name

import django

django.setup()
from BaseClass import *
from scrapy import signals
from WebDriver import SeleniumResponse
store_url = sys.argv[4]


class PromgirlsScrapper(Spider_BaseClass):
    Spider_BaseClass.cookiesDict = {"currency": "USD", "currencyOverride": "USD"}
    Spider_BaseClass.hasDriver = True
    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(PromgirlsScrapper, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        return spider

    def GetProductUrls(self, homePageResponse):
        top_category_nodes = homePageResponse.xpath(
            "(//ul[contains(@class,'nav-primary')]/li[a[not(contains(text(),'Shoes')) and not(contains(text(),'Guide')) and  not(contains(text(),'New'))]])[1]")
        for top_category_node in top_category_nodes:
            top_category_title = top_category_node.xpath("./a/text()").get().strip()
            print("TopLink :",top_category_title)
            category_nodes = top_category_nodes.xpath(
                "(./ul/li[a[contains(@class,'category')][not(contains(text(),'All'))]])[1]")
            for category_node in category_nodes:
                category_title = category_node.xpath("./a/text()").get().strip()
                sub_category_nodes = category_node.xpath("(./a[not(contains(text(),'by')) and not(contains(text(),'All')) and not(contains(text(),'SHOP'))])[1]")
                for sub_category_node in sub_category_nodes:
                    sub_category_title = sub_category_node.xpath("./text()").get().strip()
                    sub_category_link = sub_category_node.xpath("./@href").get()
                    print("title :",sub_category_title)
                    if not sub_category_link.startswith(store_url):
                        sub_category_link = store_url + sub_category_link
                    print("Sub Link: ",sub_category_link)
                    category = top_category_title + " " + category_title + " " + sub_category_title
                    # self.listing(sub_category_link, category)
        return Spider_BaseClass.AllProductUrls
    def listing(self, categorylink, category):
        seleniumResponse = SeleniumResponse(categorylink)
        product_list = seleniumResponse.xpath("//h3[@class='product-title']/a/@href").extract()
        for product_url in product_list:
            if not product_url.startswith(store_url):
                product_url = (store_url.rstrip('/') + product_url).split("&type")[0]
            print("URL :",product_url)
            Spider_BaseClass.AllProductUrls.append(product_url)
            siteMapCategory = str(Spider_BaseClass.ProductUrlsAndCategory.get(product_url)).replace('None', '')
            if siteMapCategory:
                Spider_BaseClass.ProductUrlsAndCategory[product_url] = siteMapCategory + " " + category
            else:
                Spider_BaseClass.ProductUrlsAndCategory[product_url] = category
        try:
            next_page_url = seleniumResponse.xpath("//link[@rel='next']/@href").get()
            if not next_page_url.startswith(store_url):
                next_page_url = store_url + next_page_url
            self.listing(next_page_url, category)
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
        name = str(response.xpath("//h1[@itemprop='name']/text()").get().strip()).replace(
            '’', '').replace('‘', '')
        if not color == '' and not re.search(color, name):
            name = name + ' - ' + color
        return name

    def GetSelectedColor(self, response):
        color = response.xpath("//select[@id='color']/option/text()").get().strip()
        return color
    def GetPrice(self, response):
        orignalPrice = response.xpath("//strong[@class='old']/text()")
        if orignalPrice:
            return float(str(orignalPrice.get().strip()).replace('$', '').replace(',', ''))
        else:
            regularPrice = response.xpath(
                "//h4[@itemprop='price']/text()").get().strip()
            return float(str(regularPrice).replace('$', '').replace(',', ''))
    def GetSalePrice(self, response):
        salePrice = response.xpath(
            "//h4[@itemprop='price']//span/text()")
        if salePrice:
            return float(str(salePrice.get().strip()).replace('$', '').replace(',', ''))
        else:
            return 0

    def GetDescription(self, response):
        try:
            descriptionList = response.xpath(
                "//div[@id='accordion']//text()").extract()
            description = ' '.join(descriptionList)
        except:
            description = ''

        return description

    def GetBrand(self, response):
        brand = "PROMGIRL"
        return brand
    def GetImageUrl(self, response):
        imageUrls = []
        images = response.xpath("//div[@class='slide']/a/@href").extract()
        for image in images:
            imageUrls.append(image)
        return imageUrls
    def GetSizes(self, response):
        sizes = []
        sizeList = response.xpath(
            "//select[@id='size']/option[not(contains(text(),'Select'))]/text()").extract()
        gender = ProductFilters.objects.get(ProductUrl=GetterSetter.ProductUrl).ParentCategory.split(',')[0]
        color = self.GetSelectedColor(response)
        for size in sizeList:
            available = True
            fitType = GetFitType(gender, str(size).strip())
            sizes.append([color, str(size).strip(), available, fitType, 0.0, 0.0])
        return sizes
    def GetCategory(self, response):
        siteMapCategory = str(Spider_BaseClass.ProductUrlsAndCategory.get(GetterSetter.ProductUrl)).replace('None', '')
        return "Women " + siteMapCategory + "dress "
