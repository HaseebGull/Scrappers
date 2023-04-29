import sys
from pathlib import Path

DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(DIR.parent.parent.parent.parent))
__package__ = DIR.name

import django

django.setup()
from BaseClass import *
from scrapy import signals

product_url = sys.argv[6]
store_url = sys.argv[4]


class SixpmScrapper(Spider_BaseClass):
    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(SixpmScrapper, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        return spider

    def GetProductUrls(self, homePageResponse):
        # ========== Category And Subcategory ==========#
        genderNodes = homePageResponse.xpath(
            "//div[@data-sub-nav='true']/ul/li[a[contains(text(),'Women') or contains(text(),'Men') or contains(text("
            "),'Kid')]]")
        for genderNode in genderNodes:
            genderName = genderNode.xpath("./a/text()").get().strip()
            topCategoryNodes = genderNode.xpath(
                ".//div/a[contains(text(),'Clothing') or contains(text(),'Boy') or contains(text(),'Girl')]")
            for topCategoryNode in topCategoryNodes:
                topCategoryName = topCategoryNode.xpath("./text()").get().strip()
                topCategoryUrl = topCategoryNode.xpath("./@href").get()
                if not topCategoryUrl.startswith(store_url):
                    topCategoryUrl = store_url.rstrip('/') + topCategoryUrl
                if re.search('\?', topCategoryUrl):
                    topCategoryUrl = 'https' + topCategoryUrl.split('https' or 'http')[1].split('?')[0].strip()
                topCategoryResponse = HtmlResponse(url=topCategoryUrl, body=requests.get(topCategoryUrl).text,
                                                   encoding='utf-8')
                womenXPath = "//div[contains(@id,'searchFilter')]//section[h3/button[contains(text()," \
                             "'Category')]]/div/ul/li/a[span[contains(text(),'Dress') or contains(text(),'Sets') or " \
                             "contains(text(),'Jumpsuit') or contains(text(),'Romper') or contains(text()," \
                             "'One Piece')]] "
                menXPath = "//div[contains(@id,'searchFilter')]//section[h3/button[contains(text()," \
                           "'Category')]]/div/ul/li/a[span[contains(text(),'Shirt') or contains(text(),'Coat') or " \
                           "contains(text(),'Pant') or contains(text(),'Suit') or contains(text(),'Sets') or " \
                           "contains(text(),'Jumpsuit') or contains(text(),'Romper') or contains(text(),'One Piece')]] "
                if 'Women' in genderName:
                    categoryNodes = topCategoryResponse.xpath(womenXPath)
                elif 'Men' in genderName:
                    categoryNodes = topCategoryResponse.xpath(menXPath)
                else:
                    kidsClothingUrl = topCategoryResponse.xpath(
                        "//div[contains(@id,'searchFilter')]//section[h3/button[contains(text(),'Product "
                        "Type')]]/div/ul/li/a[span[contains(text(),'Clothing')]]/@href").get()

                    if not kidsClothingUrl.startswith(store_url):
                        kidsClothingUrl = store_url.rstrip('/') + kidsClothingUrl

                    if re.search('\?', kidsClothingUrl):
                        kidsClothingUrl = 'https' + kidsClothingUrl.split('https' or 'http')[1].split('?')[0].strip()

                    kidsClothingResponse = HtmlResponse(url=kidsClothingUrl, body=requests.get(kidsClothingUrl).text,
                                                        encoding='utf-8')
                    if 'Boy' in topCategoryName:
                        categoryNodes = kidsClothingResponse.xpath(menXPath)
                    else:
                        categoryNodes = kidsClothingResponse.xpath(womenXPath)
                for categoryNode in categoryNodes:
                    categoryName = categoryNode.xpath("./span/text()").get().strip()
                    if 'Outerwear Pants' in categoryName:
                        continue
                    categoryUrl = categoryNode.xpath("./@href").get()
                    if not categoryUrl.startswith(store_url):
                        categoryUrl = store_url.rstrip('/') + categoryUrl
                    if re.search('\?', categoryUrl):
                        categoryUrl = 'https' + categoryUrl.split('https' or 'http')[1].split('?')[0].strip()
                    categoryResponse = HtmlResponse(url=categoryUrl, body=requests.get(categoryUrl).text,
                                                    encoding='utf-8')
                    subCategoryNodes = categoryResponse.xpath(
                        "//div[contains(@id,'searchFilter')]//section[h3/button[contains(text(),"
                        "'Dress Types')]]/div/ul/li/a")
                    if not subCategoryNodes:
                        subCategoryNodes = categoryResponse.xpath(
                            "//div[contains(@id,'searchFilter')]//section[h3/button[contains(text(),'Subcategory') or "
                            "contains(text(), 'Styles')]]/div/ul/li/a[span[contains(text(),'Dress Shirt') or "
                            "contains(text(),'Blazer') or contains(text(),'Trousers') or contains(text(),'Chinos')]]")
                    if subCategoryNodes:
                        for subCategoryNode in subCategoryNodes:
                            subCategoryName = subCategoryNode.xpath("./span/text()").get().strip()
                            subCategoryUrl = subCategoryNode.xpath("./@href").get().strip()
                            if not subCategoryUrl.startswith(store_url):
                                subCategoryUrl = store_url.rstrip('/') + subCategoryUrl
                            if re.search('\?', subCategoryUrl):
                                subCategoryUrl = 'https' + subCategoryUrl.split('https' or 'http')[1].split('?')[
                                    0].strip()
                            category = genderName + " " + topCategoryName + " " + categoryName + " " + subCategoryName
                            self.listing(subCategoryUrl, category)
                    else:
                        category = genderName + " " + topCategoryName + " " + categoryName
                        self.listing(categoryUrl, category)
        return Spider_BaseClass.AllProductUrls

    def listing(self, categoryUrl, category):
        typeResponse = requests.get(categoryUrl)
        typeResponse = HtmlResponse(url=categoryUrl, body=typeResponse.text, encoding='utf-8')

        product_list = typeResponse.xpath("//a[@itemprop='url']/@href").extract()
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
            nextPageUrl = typeResponse.xpath("//link[@rel='next']/@href").extract()[0]
            if not nextPageUrl.startswith(store_url):
                nextPageUrl = store_url.rstrip('/') + nextPageUrl
            self.listing(nextPageUrl, category)
        except:
            pass

    def GetProducts(self, response):
        global productData
        if re.search('window.__INITIAL_STATE__ = {', response.text):
            productJsonStr = '{' + response.text.split('window.__INITIAL_STATE__ = {')[1].split(';</script>')[0].strip()
            productData = json.loads(productJsonStr)
        ignorProduct = self.IgnoreProduct(response)
        if ignorProduct:
            self.ProductIsOutofStock(GetterSetter.ProductUrl)
        else:
            global selectedColourJson
            listCount = 0
            for colourOptions in productData["product"]["detail"]["styles"]:
                if colourOptions["productUrl"] in GetterSetter.ProductUrl:
                    selectedColourJson = json.loads(json.dumps(productData["product"]["detail"]["styles"][listCount]))
                    break
                listCount = listCount + 1
            self.GetProductInfo(response)

    def IgnoreProduct(self, response):
        if not productData["product"]["detail"]["oos"]:
            return False
        else:
            return True

    def GetName(self, response):
        color = self.GetSelectedColour()
        name = productData["product"]["detail"]["productName"]
        return name + " " + color

    def GetSelectedColour(self):
        return selectedColourJson["color"]

    def GetPrice(self, response):
        return float(selectedColourJson["originalPrice"].replace("$", ""))

    def GetSalePrice(self, response):
        return float(selectedColourJson["price"].replace("$", ""))

    def GetBrand(self, response):
        return productData["product"]["detail"]["brandName"]

    def GetImageUrl(self, response):
        imageUrls = []
        for imageToken in selectedColourJson["images"]:
            imageUrl = "https://m.media-amazon.com/images/I/" + imageToken["imageId"] + "._AC_SR736,920_.jpg"
            imageUrls.append(imageUrl)
        return imageUrls

    def GetDescription(self, response):
        description = productData["product"]["detail"]["description"]["bulletPoints"]
        return ' '.join(map(str, description))

    def GetSizes(self, response):
        productSizes = []
        # productName = self.GetName(response)
        selectedColor = self.GetSelectedColour()
        gender = ProductFilters.objects.get(ProductUrl=GetterSetter.ProductUrl).ParentCategory.split(',')[0]
        for sizeToken in selectedColourJson["stocks"]:
            available = True
            colourName = selectedColor
            sizeName = sizeToken["size"]
            fitType = GetFitType(gender, sizeName)
            productSizes.append(
                (str(colourName).title(), str(sizeName), available, str(fitType).title(), 0.0, 0.0))
        return productSizes

    def GetCategory(self, response):
        filterList = []
        for filterToken in selectedColourJson["taxonomyAttributes"]:
            filterList.append(filterToken["value"])
        filters = ' '.join(set(filterList))
        siteMapCategory = str(Spider_BaseClass.ProductUrlsAndCategory.get(GetterSetter.ProductUrl)).replace('None', '')
        return (Spider_BaseClass.testingGender + " " + siteMapCategory + " " + filters).strip()
