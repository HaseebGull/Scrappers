import sys
from pathlib import Path
from WebDriver import SeleniumResponse
DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(DIR.parent.parent.parent.parent))
__package__ = DIR.name

import django

django.setup()
from Shopify import *
from BaseClass import Spider_BaseClass
from scrapy import signals

store_url = sys.argv[4]


class AtterleyScrapper(Spider_BaseClass):
    Spider_BaseClass.cookiesDict = {"currency": "USD", "currencyOverride": "USD"}
    Spider_BaseClass.hasDriver = True
    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(AtterleyScrapper, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        return spider

    def GetProductUrls(self, homePageResponse):
        # ========== Category And Subcategory ==========#
        top_category_nodes = homePageResponse.xpath(
            "(//div[@class='desktop-navLink'][a])[1]")
        for top_category_node in top_category_nodes:
            top_category_title = top_category_node.xpath("./a/text()").get().strip()
            top_category_link = top_category_node.xpath("./a/@href").get()
            if not top_category_link.startswith(store_url):
                top_category_link = store_url.rstrip('/') + top_category_link
            print("TOP CATEGORY  :", top_category_title, "TOP CATEGORY LINK  :", top_category_link)
            category_nodes = top_category_node.xpath(
                "(.//div[contains(@id,'top-bar')]//ul[@id='nav']/li[a[contains(text(),'Clothing')]])[1]")
            for category_node in category_nodes:
                category_title = category_node.xpath("./a/text()").get().strip()
                category_link = category_node.xpath("./a/@href").get()
                if not category_link.startswith(store_url):
                    category_link = store_url.rstrip('/') + category_link
                print("CATEGORY  :", category_title, "CATEGORY LINK  :", category_link)
                sub_category_nodes = category_node.xpath(
                    "(.//div[contains(@class,'shop-by-category')]/div/ul/li/a[contains(text(),'Dresses') or contains(text(),'Jumpsuits') or contains(text(),'Nightwear') or contains(text(),'Suits') or contains(text(),'Trousers')])[1]")
                for sub_category_node in sub_category_nodes:
                    sub_category_title = sub_category_node.xpath("./text()").get().strip()
                    subCategory_link = sub_category_node.xpath("./@href").get()
                    if not subCategory_link.startswith(store_url):
                        subCategory_link = store_url.rstrip('/') + subCategory_link
                    if "Women" in top_category_link or "Trousers" in sub_category_title:
                        continue
                    print("SUB CATEGORY  :", sub_category_title, "SUB CATEGORY LINK  :", subCategory_link)
                    category = top_category_title + " " + category_title + " " + sub_category_title
                    self.listing(subCategory_link, category)
        return Spider_BaseClass.AllProductUrls

    def listing(self, subCategorylink, category):
        subCategoryLinkResponse = SeleniumResponse(subCategorylink)
        product_list = subCategoryLinkResponse.xpath(
            "(//div[contains(@class,'product-listing')]/div/div/a[contains(@class,'product-link')]/@href")[1].extract()
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
            nextPageUrl = subCategoryLinkResponse.xpath("//div[contains(@class,'next')]/a/@href").extract()[0]
            if not nextPageUrl.startswith(store_url):
                nextPageUrl = store_url.rstrip('/') + nextPageUrl
                print("NEXT PAGE :", nextPageUrl)
            self.listing(nextPageUrl, category)
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
        name = response.xpath("//div[@class='mb20 pName']/text()").get().strip()
        return name

    def GetSelectedColor(self, response):
        return "color"

    def GetPrice(self, response):
        orignalPrice = response.xpath(
            "//div[@class='price serif']/div[@class='price-box']/p[@class='old-price']/span/text()").get()
        if orignalPrice != None:
            # return float(str(orignalPrice).replace('$', '').replace(',', ''))
            return float(str(orignalPrice).replace("Â£", '').replace("£", ''))
        else:
            orignalPrice = response.xpath(
                "//div[contains(@class,'product-detail-info')]/div/div[@class='price']/span/text()").get()
            # return float(str(orignalPrice).replace('$', '').replace(',', ''))
            return float(str(orignalPrice).replace("Â£", '').replace("£", ''))

    def GetSalePrice(self, response):
        salePrice = response.xpath(
            "//div[@class='price serif']/div[@class='price-box']/p[@class='special-price']/span/text()").get()
        if salePrice != None:
            return float(str(salePrice).replace("Â£", "").replace("£", ''))
        else:
            return 0

    def GetBrand(self, response):
        return response.xpath("//div[@class='mb20 pName']/text()").get().split(' ')[0]

    def GetImageUrl(self, response):
        imageUrls = []
        if re.search('productGallery:', response.text):
            imageList = response.text.split('productGallery:')[1].split('},attribute')[0]
            jtxt = re.sub(r'\b([a-zA-Z]+):("[^"]+"[,\n}])', r'"\1":\2', imageList).replace(',video:null',
                                                                                           ',"video":null')
            imageJson = json.loads(jtxt)
            for image in imageJson:
                imageurl = image['src']
                imageUrls.append(imageurl)
        print(imageUrls)
        return imageUrls

    def GetDescription(self, response):
        return ' '.join(response.xpath("//div[@id='proDesc']/p/text()").extract()).strip()

    def GetSizes(self, response):
        sizes = []
        sizeList = response.xpath(
            "//div[@style='display:contents']/button[not(contains(@class,'outstock'))]/span")
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
        return "Women " + "Men "+ siteMapCategory
