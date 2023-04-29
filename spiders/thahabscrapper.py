import sys
from pathlib import Path

DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(DIR.parent.parent.parent.parent))
__package__ = DIR.name

import django

django.setup()
from Shopify import *
from scrapy import signals

store_url = sys.argv[4]


class Thahabscrapper(shopify):
    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(Thahabscrapper, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        return spider

    def GetProductUrls(self, homePageResponse):
        # ========== Category And Subcategory ==========#
        genderNodes = homePageResponse.xpath(
            "//div[contains(@id,'separation-menu-item')][a[contains(text(),'WOMEN') or contains(text(),'MEN')]]")
        for genderNode in genderNodes:
            genderTitle = genderNode.xpath("./a/text()").get().strip()
            # genderlink = genderNode.xpath("./a/@href").get()
            topCategoryNodes = genderNode.xpath(
                "./div/header/div/div/nav[contains(@class,'Header__MainNav')]/ul/li[a[contains(text(),'Clothing') or contains(text(),'Sale')]]")
            for topCategoryNode in topCategoryNodes:
                topCategoryTitle = topCategoryNode.xpath("./a/text()").get().strip()
                topCategorylink = topCategoryNode.xpath("./a/@href").get()
                if not topCategorylink.startswith(store_url):
                    topCategorylink = store_url.rstrip('/') + topCategorylink
                categoryNodes = topCategoryNode.xpath(
                    "./div/div/div[a[contains(text(),'Clothing') or contains(text(),'Sale')]]")
                for categoryNode in categoryNodes:
                    categoryTitle = categoryNode.xpath("./a/text()").get().strip()
                    # categorylink = categoryNode.xpath("./a/@href").get()
                    subCategoryNodes = categoryNode.xpath(
                        "./ul/li[a[contains(text(),'Dresses') or contains(text(),'Jumpsuits') or contains(text(),'Evening') or contains(text(),'Clothing') and not(contains(text(),'All'))]]")
                    for subCategoryNode in subCategoryNodes:
                        subCategoryTitle = subCategoryNode.xpath("./a/text()").get().strip()
                        subCategorylink = subCategoryNode.xpath("./a/@href").get()
                        if not subCategorylink.startswith(store_url):
                            subCategorylink = store_url.rstrip('/') + subCategorylink
                        category = genderTitle + " " + topCategoryTitle + " " + categoryTitle + " " + subCategoryTitle
                        self.listing(subCategorylink, category)
        return Spider_BaseClass.AllProductUrls

    def listing(self, categorylink, category):
        categoryLinkResponse = requests.get(categorylink)
        categoryLinkResponse = HtmlResponse(url=categorylink, body=categoryLinkResponse.text, encoding='utf-8')
        product_list = categoryLinkResponse.xpath("//div[contains(@class,'ProductItem ')]/div/a/@href").extract()
        for productUrl in product_list:
            if not productUrl.startswith(store_url):
                productUrl = store_url.rstrip('/') + productUrl
            productUrl = self.GetCanonicalUrl(productUrl)
            Spider_BaseClass.AllProductUrls.append(productUrl)
            siteMapCategory = str(Spider_BaseClass.ProductUrlsAndCategory.get(productUrl)).replace('None', '')
            if siteMapCategory:
                Spider_BaseClass.ProductUrlsAndCategory[productUrl] = siteMapCategory + " " + category
            else:
                Spider_BaseClass.ProductUrlsAndCategory[productUrl] = category
        try:
            nextPageUrl = categoryLinkResponse.xpath("//link[@rel='next']/@href").extract()[0]
            if not nextPageUrl.startswith(store_url):
                nextPageUrl = store_url.rstrip('/') + nextPageUrl
            self.listing(nextPageUrl, category)
        except:
            pass

    def GetProducts(self, response):
        ignorProduct = self.IgnoreProduct(response)
        if ignorProduct == True:
            self.ProductIsOutofStock(GetterSetter.ProductUrl)
        shopify.productJson = json.loads(self.SetProductJson(response))
        categoryAndName = shopify.GetCategory(self, response) + " " + self.GetName(response)
        if (re.search(r'\b' + 'sale' + r'\b', categoryAndName, re.IGNORECASE) or
            re.search(r'\b' + 'evening' + r'\b', categoryAndName, re.IGNORECASE) or
            re.search(r'\b' + 'new arrival' + r'\b', categoryAndName, re.IGNORECASE)) and not re.search(
            r'\b((shirt(dress?)|jump(suit?)|dress|romper|overall|gown|suit|caftan)(s|es)?)\b',
            categoryAndName, re.IGNORECASE):
            print('Skipping Non Dress Product')
            self.ProductIsOutofStock(GetterSetter.ProductUrl)
        else:
            self.GetProductInfo(response)

    def GetName(self, response):
        color = self.GetSelectedColor(response)
        name = shopify.GetName(self, response)
        if not color == '' and not re.search(color, name):
            name = name + " - " + color
        return name

    def GetSelectedColor(self, response):
        return response.xpath(
            "//span[contains(@class,'ProductForm__Label') and contains(text(), 'Color' )]/span/text()").get().strip()

    def GetSizes(self, response):
        sizes = shopify.GetSizes(self, response)
        sizeList = []
        for size in sizes:
            if not size[1] == 'Onesize':
                SizeName = size[1].split('_')[1].strip()
            else:
                SizeName = size[1]
            MappedSize = size[0], SizeName, size[2], size[3], size[4], size[5]
            sizeList.append(MappedSize)
        return sizeList

    def IgnoreProduct(self, response):
        if re.search('"availability":"', response.text):
            productAvailability = response.text.split('"availability":"')[1].split('"}}')[0].strip()
            if not 'InStock' in productAvailability or 'PreOrder' in productAvailability:
                return True
            else:
                return False
