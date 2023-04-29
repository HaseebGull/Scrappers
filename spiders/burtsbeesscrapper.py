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


class burtsbeesScrapper(magento):
    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(burtsbeesScrapper, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        return spider

    def GetProductUrls(self, homePageResponse):
        # ========== Category And Subcategory ==========#
        topCategoryNodes = homePageResponse.xpath(
            "//nav[@class='navigation']/ul/li[a[contains(span/text(),'celebration pjs') or contains(span/text(),'essentials ') or contains(span/text(),'baby') or contains(span/text(),'toddler') or contains(span/text(),'kids') or contains(span/text(),'new') or contains(span/text(),'sale')]]")
        for topCategoryNode in topCategoryNodes:
            topCategoryTitle = topCategoryNode.xpath("./a/span/text()").get().strip()
            if topCategoryTitle == 'essentials':
                topCategoryTitle = "Baby " + topCategoryTitle
            topCategorylink = topCategoryNode.xpath("./a/@href").get()
            if not topCategorylink.startswith(store_url):
                topCategorylink = store_url.rstrip('/') + topCategorylink
            categoryNodes = topCategoryNode.xpath(
                "./div//div[@class='submenu__wrapper']//div[p/a[contains(text(),'celebration pjs') or contains(text(),'Shop All') or contains(text(),'essentials') or contains(text(),'shop clothing') or contains(text(),'TODDLER') or contains(text(),'KIDS') or contains(text(),'SALE')]]")
            for categoryNode in categoryNodes:
                categoryTitle = categoryNode.xpath("./p/a/text()").get().strip()
                categorylink = categoryNode.xpath("./p/a/@href").get()
                if not categorylink.startswith(store_url):
                    categorylink = store_url.rstrip('/') + categorylink
                subCategoryNodes = categoryNode.xpath(
                    "./ul/li[a[contains(span/text(),'bodysuits') or contains(span/text(),'dress') "
                    "or contains(span/text(),'gown') or contains(span/text(),'jumpsuits') or"
                    " contains(span/text(),'clothing') or contains(text(),'bodysuits') or contains(text(),'gowns') "
                    "or contains(text(),'jumpsuits') or contains(text(),'dresses') or contains(span/text(),'pajamas')]]")
                for subCategoryNode in subCategoryNodes:
                    subCategoryTitle = subCategoryNode.xpath("./a/span/text()")
                    if subCategoryTitle:
                        subCategoryTitle = subCategoryTitle.get().strip()
                    else:
                        subCategoryTitle = subCategoryNode.xpath("./a/text()").get()
                    subCategorylink = subCategoryNode.xpath("./a/@href").get()
                    if not subCategorylink.startswith(store_url):
                        subCategorylink = store_url.rstrip('/') + subCategorylink
                    # =================== BREADCRUM =================== #
                    category = topCategoryTitle + " " + categoryTitle + " " + subCategoryTitle
                    # ======================================#
                    self.listing(subCategorylink, category)
        return Spider_BaseClass.AllProductUrls

    def listing(self, categorylink, category):
        CategoryLinkResponse = requests.get(categorylink)
        categoryPageResponse = HtmlResponse(url=categorylink, body=CategoryLinkResponse.text, encoding='utf-8')
        product_list = categoryPageResponse.xpath(
            "//a[@class='product-item-link']/@href").extract()
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
            nextpageUrl = \
                categoryPageResponse.xpath("//a[@title='Next']/@href").extract()[0]
            if not nextpageUrl.startswith(store_url):
                nextpageUrl = store_url.rstrip('/') + nextpageUrl
            self.listing(nextpageUrl, category)
        except:
            pass

    def GetProducts(self, response):
        ignorProduct = self.IgnoreProduct(response)
        if ignorProduct == True:
            self.ProductIsOutofStock(GetterSetter.ProductUrl)
        else:
            jsonStr = self.SetProductJson(response.text)
            categoryAndName = self.GetCategory(response) + " " + self.GetName(response)
            if (re.search(r'\bSALE clothing\b', categoryAndName, re.IGNORECASE) or
                re.search(r'\bKIDS clothing\b', categoryAndName, re.IGNORECASE)
                or re.search(r'\bTODDLER clothing\b', categoryAndName, re.IGNORECASE)) and not \
                    re.search(
                        r'\b((shirt(dress?)|jump(suit?)|dress|gown|set|footie|romper|footed pajama|overall|body(suit?)|suit|caftan)(s|es)?)\b',
                        categoryAndName,
                        re.IGNORECASE):
                print('Skipping Non Dress Product')
                self.ProductIsOutofStock(GetterSetter.ProductUrl)
            else:
                if jsonStr != '':
                    magento.productJson = json.loads(jsonStr)
                global productID
                productID = response.xpath("//input[@name='product']/@value").get()
                self.GetProductInfo(response)

    def SetProductJson(self, response):
        if re.search('"jsonConfig": ', response):
            magento.productJson = response.split('"jsonConfig": ')[1].split('"jsonSwatchConfig": ')[0].rstrip().rstrip(
                ',')
        return magento.productJson

    def GetName(self, response):
        return response.xpath("//div[contains(@class,'page-title-wrapper')]/h1/span/text()").get().strip()

    def GetPrice(self, response):
        orignalPrice = response.xpath(
            "//div[@class='product-info-price']/div/span[@class='normal-price']/span//span/text()").get()
        if orignalPrice != None:
            return float(str(orignalPrice).replace('$', '').replace(',', ''))
        else:
            regularPrice = response.xpath(
                "//div[@class='product-info-price']/div/span[contains(@class,'old-price')]/span//span/text()").get()
            return float(str(regularPrice).replace('$', '').replace(',', ''))

    def GetSalePrice(self, response):
        salePrice = response.xpath(
            "//div[@class='product-info-price']/div/span[@class='special-price']/span//span/text()").get()
        if salePrice:
            return float(str(salePrice).replace('$', '').replace(',', ''))
        else:
            return 0

    def GetImageUrl(self, response):
        imageUrl = []
        data = response.xpath(
            "//script[@type='text/x-magento-init' and contains(text(),'gallery/gallery')]").get()
        if data:
            imageJsonStr = '{"data":' + data.split('data":')[1].split('}],')[0].strip().rstrip(',') + '}]}'
            imageJson = json.loads(imageJsonStr)
            for imageToken in imageJson['data']:
                imageUrl.append(imageToken['img'])
        return imageUrl

    def GetDescription(self, response):
        return ','.join(
            response.xpath("//div[contains(@class,'description')]//div/p/following-sibling::ul/li/text()").extract())

    def GetBrand(self, response):
        return "burt's bees baby"

    def GetCategory(self, response):
        siteMapCategory = str(Spider_BaseClass.ProductUrlsAndCategory.get(GetterSetter.ProductUrl)).replace('None', '')
        return siteMapCategory

    def IgnoreProduct(self, response):
        productAvailability = response.xpath(
            "//div[@class='product-hero__info']//div/div[@title='Availability']/span/text()").get()
        if 'InStock' in productAvailability:
            return True
        else:
            return False
