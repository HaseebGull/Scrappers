import sys
from pathlib import Path

DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(DIR.parent.parent.parent.parent))
__package__ = DIR.name

import django

django.setup()
from BaseClass import *
from scrapy import signals
from seleniumfile import SeleniumResponse

store_url = sys.argv[4]


class ForeverTwentyoneScrapper(Spider_BaseClass):
    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(ForeverTwentyoneScrapper, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        return spider

    def GetProductUrls(self, homePageResponse):
        # ========== Category And Subcategory ==========#
        # seleniumResponse = SeleniumResponse(store_url)
        # topCategoryNodes = seleniumResponse.xpath(
        #     "//ul[contains(@class,'header-flyout__list level-1')]/li[a/following-sibling::label[contains(text(),"
        #     "'Women') or contains(text(),'Plus') or contains(text(),'Men') or contains(text(),'Girl') or contains("
        #     "text(),'Sale')]]")
        # for topCategoryNode in topCategoryNodes:
        #     topCategoryTitle = topCategoryNode.xpath("./a/following-sibling::label/text()").get().strip()
        #     topCategorylink = topCategoryNode.xpath("./a/@href").get()
        #     if not topCategorylink.startswith(store_url):
        #         topCategorylink = store_url.rstrip('/') + topCategorylink
        #
        #     categoryNodes = topCategoryNode.xpath(
        #         """./div[@aria-label='Sub menu']/ul/li[contains(@class,'header-flyout__column level-2 ')][a[contains(
        #         text(),'New') or contains(text(),'Clothing') or contains(text(),"Women's") or contains(text(),
        #         "Men's") and not(contains(text(),'Accessories')) or contains(text(),'Plus + Curve') and not(contains(
        #         text(),'Shop All')) or contains(text(),'Kids')]]""")
        #     for categoryNode in categoryNodes:
        #         categoryTitle = categoryNode.xpath("./a/text()").get().strip()
        #         categorylink = categoryNode.xpath("./a/@href").get()
        #         if not categorylink.startswith(store_url):
        #             categorylink = store_url.rstrip('/') + categorylink
        #
        #         subCategoryNodes = categoryNode.xpath(
        #             "./ul/li/a[contains(text(),'Dress') or contains(text(),'New') or contains(text(),'Rompers + Jumpsuits')]")
        #         for subCategoryNode in subCategoryNodes:
        #             subCategoryTitle = subCategoryNode.xpath("./text()").get().strip()
        #             subCategorylink = subCategoryNode.xpath("./@href").get()
        #             if not subCategorylink.startswith(store_url):
        #                 subCategorylink = store_url.rstrip('/') + subCategorylink
        #             if (topCategoryTitle == 'Sale' or topCategoryTitle == 'Girls + Boys') and (
        #                     categoryTitle == 'Kids' or categoryTitle == 'Shop All Girls + Boys'):
        #                 category = topCategoryTitle + " " + categoryTitle + " " + subCategoryTitle
        #             else:
        #                 if 'Women' in topCategoryTitle:
        #                     category = topCategoryTitle + " " + categoryTitle + " " + subCategoryTitle
        #                 else:
        #                     category = 'Women ' + topCategoryTitle + " " + categoryTitle + " " + subCategoryTitle
        #             self.listing(subCategorylink, category)
        url = 'https://www.forever21.com/us/2000459654.html'
        Spider_BaseClass.ProductUrlsAndCategory[url] = 'Women'
        Spider_BaseClass.AllProductUrls.append(url)
        return Spider_BaseClass.AllProductUrls

    def listing(self, categorylink, category):
        categoryLinkResponse = SeleniumResponse(categorylink)
        product_list = categoryLinkResponse.xpath(
            "//a[@class='product-tile__anchor']/@href").extract()
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
            nextpageUrl = categoryLinkResponse.xpath("//a[@href='pagination.next.url']/button/@data-url").get()
            if not nextpageUrl.startswith(store_url):
                nextpageUrl = store_url.rstrip('/') + nextpageUrl
            self.listing(nextpageUrl, category)
        except:
            pass

    def GetCategories(self, response):
        url = response.request.url
        ConvertedResponse = SeleniumResponse(url)
        Spider_BaseClass.AllProductUrl = list(set(self.GetProductUrls(ConvertedResponse)))

        print('DB Urls', len(Spider_BaseClass.db_urls))
        print('Web Urls', len(Spider_BaseClass.AllProductUrl))
        print('DB & Web Urls', len(Spider_BaseClass.AllProductUrl) + len(Spider_BaseClass.db_urls))

        Spider_BaseClass.TotalDistinctProductUrl = list(set(Spider_BaseClass.AllProductUrl + Spider_BaseClass.db_urls))
        print('Distinct Urls', len(Spider_BaseClass.TotalDistinctProductUrl))

        Product.objects.filter(StoreId=store_id).update(UpdatedOrAddedOnLastRun=0)

        for productUrl in Spider_BaseClass.TotalDistinctProductUrl:
            try:
                GetterSetter.ProductUrl = productUrl
                # productres = requests.get(productUrl, cookies=Spider_BaseClass.cookiesDict,
                #                           headers=Spider_BaseClass.headersDict)
                # productResponse = HtmlResponse(url=productUrl, body=productres.text, encoding='utf-8')
                productResponse = SeleniumResponse(productUrl)
                self.GetProducts(productResponse)
            except Exception as e:
                self.ExceptionHandlineInGetProductInfo(e, 'GetProductsError',
                                                       'Exception: Exception in GetProducts function.')
                continue

    def GetProducts(self, response):
        global productJson
        productJson = json.loads(self.SetProductJson(response))
        ignorProduct = self.IgnoreProduct(response)
        if ignorProduct == True:
            self.ProductIsOutofStock(GetterSetter.ProductUrl)
        categoryAndName = self.GetCategory(response) + " " + self.GetName(response)
        if (re.search('sale', categoryAndName, re.IGNORECASE) or
            re.search('new arrival', categoryAndName, re.IGNORECASE)) and not \
                re.search(r'\b((shirt(dress?)|jump(suit?)|dress|gown|romper|suit|caftan)(s|es)?)\b', categoryAndName,
                          re.IGNORECASE):
            print('Skipping Non Dress Product')
            self.ProductIsOutofStock(GetterSetter.ProductUrl)
        else:
            self.GetProductInfo(response)

    def SetProductJson(self, response):
        productJson = response.xpath("//script[@type='application/ld+json']/text()").get().strip()
        return productJson

    def IgnoreProduct(self, response):
        productAvailability = productJson['mainEntity']['offers']['availability']
        if not 'InStock' in productAvailability or 'PreOrder' in productAvailability:
            return True
        else:
            return False

    def GetName(self, response):
        color = self.GetSelectedColor(response)
        name = productJson['name']
        if not color == '' and not re.search(color, name, re.I):
            name = name + " - " + color
        return name

    def GetSelectedColor(self, response):
        return productJson['mainEntity']['color']

    def GetPrice(self, response):
        orignalPrice = response.xpath(
            "//div[contains(@class,'pdp-main__price')]//span[contains(@class,'price__original')]/span[@itemprop='price']/text()").get().strip()
        if orignalPrice != None:
            return float(str(orignalPrice).replace("$", "").replace(',', ''))

    def GetSalePrice(self, response):
        salePrice = productJson['mainEntity']['offers']['price']
        if salePrice != None:
            return float(str(salePrice).replace("$", "").replace(',', ''))
        else:
            return 0

    def GetBrand(self, response):
        return ''

    def GetImageUrl(self, response):
        imageUrls = []
        images = productJson['mainEntity']['image']
        if images:
            for image in images:
                imageUrls.append(image)
            return imageUrls
        else:
            raise NotImplementedError('NO Images Found')

    def GetDescription(self, response):
        return productJson['mainEntity']['description']

    def GetSizes(self, response):
        productSizes = []
        colorName = self.GetSelectedColor(response)
        sizeOptions = response.xpath(
            "//button[contains(@class,'product-attribute__swatch swatch--size') and contains(@class,'selectable')]/text()").extract()
        gender = ProductFilters.objects.get(ProductUrl=GetterSetter.ProductUrl).ParentCategory.split(',')[0]
        for sizeName in sizeOptions:
            fitType = GetFitType(gender, str(sizeName).replace('\n',''))
            available = True
            sizelist = str(colorName), str(sizeName).replace('\n',''), available, str(fitType), 0.0, 0.0
            print(sizelist)
            productSizes.append(sizelist)
        return productSizes

    def GetCategory(self, response):
        siteMapCategory = str(Spider_BaseClass.ProductUrlsAndCategory.get(GetterSetter.ProductUrl)).replace('None', '')
        return siteMapCategory
