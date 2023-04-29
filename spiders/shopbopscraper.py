import sys
from pathlib import Path

DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(DIR.parent.parent.parent.parent))
__package__ = DIR.name

import django

django.setup()
from Shopify import *
from BaseClass import Spider_BaseClass
from scrapy import signals

store_url = sys.argv[4]


class ShopbopScraper(Spider_BaseClass):
    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(ShopbopScraper, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        return spider

    def GetProductUrls(self, homePageResponse):
        # ========== Category And Subcategory ==========#
        topCategoryNodes = homePageResponse.xpath(
            "//div[contains(@class,'top-nav-container')]/ul/div/li[a[contains(span/text(),'Clothing') or contains(span/text(),'Men')]]")
        for topCategoryNode in topCategoryNodes:
            topCategoryNodeTitle = topCategoryNode.xpath("./a/span/text()").get().strip()
            if not 'Men' in topCategoryNodeTitle:
                topCategoryNodeTitle = "Women" + " " + topCategoryNodeTitle
            topCategoryNodelink = topCategoryNode.xpath("./a/@href").get()
            if not topCategoryNodelink.startswith(store_url):
                topCategoryNodelink = store_url.rstrip('/') + topCategoryNodelink

            categoryNodes = topCategoryNode.xpath(
                "./div/div/section/ul/li/a[div/text()='Dresses' or contains(div/text(),'Jumpsuits & Rompers') or contains(div/text(),'Clothing') and not(contains(div/text(),'All'))]")
            for categoryNode in categoryNodes:
                categoryNodeTitle = categoryNode.xpath("./div/text()").get().strip()
                categoryNodelink = categoryNode.xpath("./@href").get()
                if not categoryNodelink.startswith(store_url):
                    categoryNodelink = store_url.rstrip('/') + categoryNodelink

                categoryLinkResponse = requests.get(categoryNodelink)
                categoryLinkResponse = HtmlResponse(url=categoryNodelink, body=categoryLinkResponse.text,
                                                    encoding='utf-8')
                subCategoryNodes = categoryLinkResponse.xpath(
                    "//ul[contains(@class,'NavCategory')]/li[a[contains(@class,'selected')]]/ul/li/a")

                if not subCategoryNodes:
                    subCategoryNodes = categoryLinkResponse.xpath(
                        "//ul[contains(@class,'NavCategory')]/li/a[contains(text(),'Pants') or text()='Shirts' or contains(text(),'Suits')]")
                    for subCategoryNode in subCategoryNodes:
                        subCategoryNodeTitle = subCategoryNode.xpath("./text()").get().strip()
                        subCategoryNodelink = subCategoryNode.xpath("./@href").get()
                        if not subCategoryNodelink.startswith(store_url):
                            subCategoryNodelink = store_url.rstrip('/') + subCategoryNodelink

                        subCategoryLinkResponse = requests.get(subCategoryNodelink)
                        subCategoryLinkResponse = HtmlResponse(url=subCategoryNodelink,
                                                               body=subCategoryLinkResponse.text,
                                                               encoding='utf-8')
                        subSubCategoryNodes = subCategoryLinkResponse.xpath(
                            "//ul[contains(@class,'NavCategory')]/li[a[contains(@class,'selected')]]/ul/li/a[contains(text(),'Dress')]")
                        if subSubCategoryNodes:
                            for subSubCategoryNode in subSubCategoryNodes:
                                subSubCategoryNodeTitle = subSubCategoryNode.xpath("./text()").get().strip()
                                subSubCategoryNodeLink = subSubCategoryNode.xpath("./@href").get()
                                if not subSubCategoryNodeLink.startswith(store_url):
                                    subSubCategoryNodeLink = store_url.rstrip('/') + subSubCategoryNodeLink

                                category = topCategoryNodeTitle + " " + categoryNodeTitle + " " + subCategoryNodeTitle + " " + subSubCategoryNodeTitle
                                self.listing(subSubCategoryNodeLink, category)

                else:
                    for subCategoryNode in subCategoryNodes:
                        subCategoryNodeTitle = subCategoryNode.xpath("./text()").get().strip()
                        subCategoryNodelink = subCategoryNode.xpath("./@href").get()
                        if not subCategoryNodelink.startswith(store_url):
                            subCategoryNodelink = store_url.rstrip('/') + subCategoryNodelink

                        category = topCategoryNodeTitle + " " + categoryNodeTitle + " " + subCategoryNodeTitle
                        self.listing(subCategoryNodelink, category)
        return Spider_BaseClass.AllProductUrls

    # def subCategory(self, response, category):
    #     subCategoryNodes = response.xpath(
    #         "//ul[contains(@class,'NavCategory')]/li[a[contains(@class,'selected')]]/ul/li/a")
    #     if subCategoryNodes:
    #         for subCategoryNode in subCategoryNodes:
    #             subCategoryNodeTitle = subCategoryNode.xpath("./text()").get().strip()
    #             subCategoryNodelink = subCategoryNode.xpath("./@href").get()
    #             if not subCategoryNodelink.startswith(store_url):
    #                 subCategoryNodelink = store_url.rstrip('/') + subCategoryNodelink
    #             category += " " + subCategoryNodeTitle
    #             categoryLinkResponse = requests.get(subCategoryNodelink)
    #             categoryLinkResponse = HtmlResponse(url=subCategoryNodelink, body=categoryLinkResponse.text,
    #                                                 encoding='utf-8')
    #             print(category)
    #             # self.listing(categoryLinkResponse, category)
    #     else:
    #         subCategoryNodes = response.xpath(
    #             "//ul[contains(@class,'NavCategory')]/li/a[contains(text(),'Pants') or text()='Shirts' or contains(text(),'Suits')]")
    #         for subCategoryNode in subCategoryNodes:
    #             subCategoryNodeTitle = subCategoryNode.xpath("./text()").get().strip()
    #             subCategoryNodelink = subCategoryNode.xpath("./@href").get()
    #             if not subCategoryNodelink.startswith(store_url):
    #                 subCategoryNodelink = store_url.rstrip('/') + subCategoryNodelink
    #             category += subCategoryNodeTitle
    #             subCategoryLinkResponse = requests.get(subCategoryNodelink)
    #             subCategoryLinkResponse = HtmlResponse(url=subCategoryNodelink, body=subCategoryLinkResponse.text,
    #                                                    encoding='utf-8')
    #             category += " " + subCategoryNodeTitle
    #             print(category)
    #             # self.subSubCategory(subCategoryLinkResponse, category)
    #
    # def subSubCategory(self, response, category):
    #     subCategoryNodes = response.xpath(
    #         "//ul[contains(@class,'NavCategory')]/li[a[contains(@class,'selected')]]/ul/li/a[contains(text(),'Dress')]")
    #     if subCategoryNodes:
    #         for subCategoryNode in subCategoryNodes:
    #             subCategoryNodeTitle = subCategoryNode.xpath("./text()").get().strip()
    #             subCategoryNodelink = subCategoryNode.xpath("./@href").get()
    #             if not subCategoryNodelink.startswith(store_url):
    #                 subCategoryNodelink = store_url.rstrip('/') + subCategoryNodelink
    #             category += subCategoryNodeTitle
    #             categoryLinkResponse = requests.get(subCategoryNodelink)
    #             categoryLinkResponse = HtmlResponse(url=subCategoryNodelink, body=categoryLinkResponse.text,
    #                                                 encoding='utf-8')
    #             self.listing(categoryLinkResponse, category)
    #
    #     else:
    #         self.listing(response, category)

    def listing(self, categorylink, category):
        categoryLinkResponse = requests.get(categorylink)
        categoryLinkResponse = HtmlResponse(url=categorylink, body=categoryLinkResponse.text,
                                            encoding='utf-8')
        product_list = categoryLinkResponse.xpath("//a[@class='url']/@href").extract()
        for productUrl in product_list:
            if not productUrl.startswith(store_url):
                productUrl = store_url.rstrip('/') + productUrl
            if re.search('https://', productUrl) and re.search('.htm', productUrl):
                productUrl = 'https://' + productUrl.split('https://')[1].split('.htm')[0].strip() + '.htm'
            Spider_BaseClass.AllProductUrls.append(productUrl)
            siteMapCategory = str(Spider_BaseClass.ProductUrlsAndCategory.get(productUrl)).replace('None', '')
            if siteMapCategory:
                Spider_BaseClass.ProductUrlsAndCategory[productUrl] = siteMapCategory + " " + category
            else:
                Spider_BaseClass.ProductUrlsAndCategory[productUrl] = category
        try:
            nextPageUrl = categoryLinkResponse.xpath(
                "(//a[contains(@class,'next') and not(contains(@class,'disabled'))]/@data-next-link)[1]").extract()[0]
            if not nextPageUrl.startswith(store_url):
                nextPageUrl = store_url.rstrip('/') + nextPageUrl
            self.listing(nextPageUrl, category)
        except:
            pass

    def GetProducts(self, response):
        ignorProduct = self.IgnoreProduct(response)
        if ignorProduct == True:
            self.ProductIsOutofStock(GetterSetter.ProductUrl)
        else:
            global productJsonStr
            if re.search('data-key="pdp.state">', response.text):
                productJsonStr = response.text.split('data-key="pdp.state">')[1].split('</script>')[0].strip()
                productJsonStr = json.loads(productJsonStr)
            self.GetProductInfo(response)

    def GetName(self, response):
        colorName = productJsonStr['product']['defaultStyleColor']['color']['label']
        name = productJsonStr['product']['shortDescription']
        if not colorName == '' and not re.search(colorName, name):
            name = name + ' - ' + colorName
        return name

    def GetPrice(self, response):
        originalPrice = productJsonStr['product']["defaultStyleColor"]['prices'][0]['retailAmount']
        return originalPrice

    def GetSalePrice(self, response):
        price = productJsonStr['product']["defaultStyleColor"]['prices'][0]['saleAmount']
        return price

    def GetBrand(self, response):
        brand = productJsonStr["product"]["brandLabel"]
        return brand

    def GetImageUrl(self, response):
        imageUrls = []
        imageTokens = productJsonStr['product']["defaultStyleColor"]['images']
        for imageToken in imageTokens:
            imageUrl = imageToken["url"]
            imageUrls.append(imageUrl)
        return imageUrls

    def GetDescription(self, response):
        description = productJsonStr["product"]["longDescription"]
        return description

    def GetSizes(self, response):
        productSizes = []
        colorName = productJsonStr['product']['defaultStyleColor']['color']['label']
        sizeTokens = productJsonStr['product']['styleColors']
        sizeScaleTag = productJsonStr['product']['sizeAndFitDetail']['sizeScale']
        gender = ProductFilters.objects.get(ProductUrl=GetterSetter.ProductUrl).ParentCategory.split(',')[0]
        for sizetoken in sizeTokens:
            for size in sizetoken['styleColorSizes']:
                if size['inStock'] == True:
                    sizename = size['size']['label']
                    fitType = GetFitType(gender, sizename)
                    sizeScale = self.GetSizeScale(gender, sizeScaleTag)
                    if sizeScale:
                        sizename = sizeScale + " " + sizename
                    available = True
                    sizeList = str(colorName), str(sizename), available, str(fitType), 0.0, 0.0
                    productSizes.append(sizeList)
        return productSizes

    def IgnoreProduct(self, response):
        productAvailability = response.xpath("//link[@itemprop='availability']/@href").get()
        if 'InStock' in productAvailability:
            return False
        else:
            return True

    def GetCategory(self, response):
        filterList = []
        siteMapCategory = str(Spider_BaseClass.ProductUrlsAndCategory.get(GetterSetter.ProductUrl)).replace('None', '')
        filter = str(productJsonStr['product']['classification']).split('/')
        filterList.append(filter)
        filters = '$'.join(map(str, filterList)) + '$'
        return siteMapCategory.strip() + filters

    def GetSizeScale(self, gender, sizeScaleTag):
        sizeScale = ''
        if 'Women' in gender:
            if 'Italian' in sizeScaleTag:
                sizeScale = 'IT'
            elif 'Netherlands' in sizeScaleTag:
                sizeScale = 'NL'
            elif 'French' in sizeScaleTag:
                sizeScale = 'FR'
            elif 'European' in sizeScaleTag:
                sizeScale = 'EUR'
            elif 'UK' in sizeScaleTag or 'AU' in sizeScaleTag:
                sizeScale = 'UK'
            elif 'Numbered' in sizeScaleTag or 'US' in sizeScaleTag or 'United State' in sizeScaleTag:
                sizeScale = 'US'
            else:
                sizeScale = ''
        elif 'Men' in gender:
            if 'Lettered' in sizeScaleTag:
                sizeScale = ''
        return sizeScale
