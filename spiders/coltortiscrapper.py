import sys
from pathlib import Path

DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(DIR.parent.parent.parent.parent))
__package__ = DIR.name

import django

django.setup()
from Magento import *
from scrapy import signals

store_url = sys.argv[4]


class ColtortiScrapper(magento):
    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(ColtortiScrapper, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        return spider

    def GetProductUrls(self, homePageResponse):
        # ========== Category And Subcategory ==========#
        topCategoryNodes = homePageResponse.xpath(
            "//nav[@class='navigation']/div/div/div[a[contains(span/text(),'Women') ]]")
        for topCategoryNode in topCategoryNodes:
            topCategoryNodeTitle = topCategoryNode.xpath("./a/span/text()").get().strip()
            topCategoryNodelink = topCategoryNode.xpath("./a/@href").get()
            if not topCategoryNodelink.startswith(store_url):
                topCategoryNodelink = store_url.rstrip('/') + topCategoryNodelink
            categoryNodes = topCategoryNode.xpath(
                "./div/div[a[contains(span/text(),'Clothing')]]")
            for categoryNode in categoryNodes:
                categoryNodeTitle = categoryNode.xpath("./a/span/text()").get().strip()
                categoryNodelink = categoryNode.xpath("./a/@href").get()
                if not categoryNodelink.startswith(store_url):
                    categoryNodelink = store_url.rstrip('/') + categoryNodelink
                subCategoryNodes = categoryNode.xpath(
                    "./div/div/a[contains(span/text(),'Dresses') or contains(span/text(),'Jumpsuits')]")
                # if not subCategoryNodes:
                #     category = topCategoryNodeTitle + " " + categoryNodeTitle
                #     self.listing(categoryNodelink, category)
                # else:
                for subCategoryNode in subCategoryNodes:
                    subCategoryNodeTitle = subCategoryNode.xpath("./span/text()").get().strip()
                    subCategoryNodelink = subCategoryNode.xpath("./@href").get()
                    if not subCategoryNodelink.startswith(store_url):
                        subCategoryNodelink = store_url.rstrip('/') + subCategoryNodelink
                    category = topCategoryNodeTitle + " " + categoryNodeTitle + " " + subCategoryNodeTitle
                    self.listing(subCategoryNodelink, category)
        return Spider_BaseClass.AllProductUrls

    def listing(self, subCategoryNodelink, category):
        subCategoryLinkResponse = requests.get(subCategoryNodelink)
        subCategoryLinkResponse = HtmlResponse(url=subCategoryNodelink, body=subCategoryLinkResponse.text,
                                               encoding='utf-8', )
        product_list = subCategoryLinkResponse.xpath("//div[@class='product-item-info']/a/@href").extract()
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
            nextPageUrl = subCategoryLinkResponse.xpath(
                "//a[@class='action  next']/@href").get()
            if not nextPageUrl.startswith(store_url):
                nextPageUrl = store_url.rstrip('/') + nextPageUrl
            self.listing(nextPageUrl, category)
        except:
            pass

    # def GetProducts(self, response):
    #     ignorProduct = self.IgnoreProduct(response)
    #     if ignorProduct == True:
    #         self.ProductIsOutofStock(GetterSetter.ProductUrl)
    #     categoryAndName = magento.GetCategory(self, response) + " " + self.GetName(response)
    #     if (re.search(r'\b' + 'Sale' + r'\b', categoryAndName, re.IGNORECASE) or
    #         re.search(r'\b' + 'New in' + r'\b', categoryAndName, re.IGNORECASE)) and not \
    #             re.search(r'\b((shirt(dress?)|jump(suit?)|dress|gown|suit|caftan)(s|es)?)\b', categoryAndName,
    #                       re.IGNORECASE):
    #         print('Skipping Non Dress Product')
    #         self.ProductIsOutofStock(GetterSetter.ProductUrl)
    #     else:
    #         jsonStr = self.SetProductJson(response.text)
    #         if jsonStr != '':
    #             magento.productJson = json.loads(jsonStr)
    #         productID = response.xpath("//input[@name='product']/@value").get()
    #         self.GetProductInfo(response)

    def SetProductJson(self, response):
        if re.search('"spConfig": ', response):
            return str(response.split('"spConfig": ')[1].split('"gallerySwitchStrategy":')[0]).strip().rstrip(',')
        return ''

    def GetName(self, response):
        return response.xpath("//div[@itemprop='name']/text()").get().strip()

    def GetSelectedColor(self, response):
        try:
            return response.xpath(
                "//div[@class='product attribute colore' and div[text()= 'Color: ']]/div[@class='value']/div/text()").get().strip()
        except:
            return ''

    def GetPrice(self, response):
        orignalPrice = response.xpath(
            "//div[@class='top-info-container']//span[@class='old-price']/span/span[@data-price-type='oldPrice']/span/text()").get()
        if orignalPrice != None:
            return float(str(orignalPrice).replace('$', '').replace(',', ''))
        else:
            regularPrice = response.xpath(
                "//div[@class='top-info-container']//span[@class='normal-price']/span/span[@data-price-type='finalPrice']/span/text()").get()
            return float(str(regularPrice).replace('$', '').replace(',', ''))

    def GetSalePrice(self, response):
        salePrice = response.xpath(
            "//div[@class='top-info-container']//span[@class='normal-price']/span/span[@data-price-type='finalPrice']/span/text()").get()
        if salePrice:
            return float(str(salePrice).replace('$', '').replace(',', ''))
        else:
            return 0

    def GetBrand(self, response):
        return response.xpath("//div[@class='product attribute manufacturer']/a/h2/text()").get().strip()

    def GetImageUrl(self, response):
        imageUrls = []
        images = response.xpath("//div[@class='imgs-container']/a/@href").extract()
        for image in images:
            imageUrls.append(image)
        return imageUrls

    def GetSizes(self, response):
        sizeList = []
        sizes = magento.GetSizes(self, response)
        color = self.GetSelectedColor(response)
        for size in sizes:
            sizeList.append([color, size[1], size[2], size[3], size[4], size[5]])
        return sizeList
