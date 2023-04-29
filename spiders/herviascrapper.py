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


class HerviaScrapper(Spider_BaseClass):
    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(HerviaScrapper, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        return spider

    def GetProductUrls(self, homePageResponse):
        # ========== Category And Subcategory ==========#
        topCategoryNodes = homePageResponse.xpath(
            "//ul[contains(@class,'mainMenu')]/li[a[span/text()='Women']]")
        for topCategoryNode in topCategoryNodes:
            topCategoryTitle = topCategoryNode.xpath("./a/span/text()").get().strip()
            topCategorylink = topCategoryNode.xpath("./a/@href").get()
            if not topCategorylink.startswith(store_url):
                topCategorylink = store_url.rstrip('/') + topCategorylink
            categoryNodes = topCategoryNode.xpath(
                "./ul/li[a[contains(text(),'Clothing') or contains(text(),'Sale') or contains(text(),'New')]]")
            for categoryNode in categoryNodes:
                categoryTitle = categoryNode.xpath("./a/text()").get().strip()
                categorylink = categoryNode.xpath("./a/@href").get()
                if not categorylink.startswith(store_url):
                    categorylink = store_url.rstrip('/') + categorylink
                subCategoryNodes = categoryNode.xpath(
                    "./ul/li/a[contains(span/text(),'Jumpsuits') or contains(span/text(),'Dresses') or contains(span/text(),'Clothing')]")
                if not subCategoryNodes:
                    category = topCategoryTitle + " " + categoryTitle
                    self.listing(categorylink, category)
                else:
                    for subCategoryNode in subCategoryNodes:
                        subCategoryTitle = subCategoryNode.xpath("./span/text()").get().strip()
                        subCategorylink = subCategoryNode.xpath("./@href").get()
                        if not subCategorylink.startswith(store_url):
                            subCategorylink = store_url.rstrip('/') + subCategorylink
                        category = topCategoryTitle + " " + categoryTitle + " " + subCategoryTitle
                        self.listing(subCategorylink, category)

        return Spider_BaseClass.AllProductUrls

    def listing(self, categorylink, category):
        categoryLinkResponse = requests.get(categorylink, stream=True)
        categoryLinkResponse = HtmlResponse(url=categorylink, body=categoryLinkResponse.text, encoding='utf-8')
        product_list = categoryLinkResponse.xpath(
            "//h5[@class='itemSmallTitle']/a/@href").extract()
        for productUrl in product_list:
            if not productUrl.startswith(store_url):
                productUrl = store_url.rstrip('/') + productUrl
            if re.search('https://', productUrl) and re.search('.html', productUrl):
                productUrl = 'https://' + productUrl.split('https://')[1].split('.html')[0].strip() + '.html'
            Spider_BaseClass.AllProductUrls.append(productUrl)
            siteMapCategory = str(Spider_BaseClass.ProductUrlsAndCategory.get(productUrl)).replace('None', '')
            if siteMapCategory:
                Spider_BaseClass.ProductUrlsAndCategory[productUrl] = siteMapCategory + " " + category
            else:
                Spider_BaseClass.ProductUrlsAndCategory[productUrl] = category
        try:
            pass
            nextPageUrl = categoryLinkResponse.xpath(
                "//a[@rel='next']/@href").get()
            if not nextPageUrl.startswith(store_url):
                nextPageUrl = store_url.rstrip('/') + nextPageUrl
            self.listing(nextPageUrl, category)
        except:
            pass

    def GetProducts(self, response):
        global productjson
        ignorProduct = self.IgnoreProduct(response)
        if ignorProduct == True:
            self.ProductIsOutofStock(GetterSetter.ProductUrl)
        else:
            categoryAndName = self.GetCategory(response) + " " + self.GetName(response)
            if (re.search('sale', categoryAndName, re.IGNORECASE) or re.search('New In', categoryAndName,
                                                                               re.IGNORECASE)) and not re.search(
                    r'\b((shirt(dress?)|jump(suit?)|dress|gown|set|romper|suit|caftan)(s|es)?)\b', categoryAndName,
                    re.IGNORECASE):
                print('Skipping Non Dress Product')
                self.ProductIsOutofStock(GetterSetter.ProductUrl)
            else:
                self.GetProductInfo(response)

    def IgnoreProduct(self, response):
        if re.search('"availability":"', response.text):
            productAvailability = response.text.split('"availability":"')[1].split('"}}')[0].strip()
            if not 'InStock' in productAvailability or 'PreOrder' in productAvailability:
                return True
            else:
                return False

    def GetName(self, response):
        # color = self.GetSelectedColor(response)
        name = str(response.xpath("//div[@class='itemTitle']/h1/text()/following-sibling::text()").get()).strip()
        # print(color)
        # print(name)
        # if not color == '' and not re.search(color, name, re.I):
        #     name = name + " - " + color
        return name

    def GetSelectedColor(self, response):
        colorName = ''
        try:
            colorUrl = response.xpath("//link[@rel='canonical']/@href").get()
            colorName = response.xpath(
                "//div[@class='colourItem'][input[contains(@data-link,'" + colorUrl + "')]]/label/text()").get().strip()
            return colorName
        except:
            description = ' '.join(response.xpath("//div[@class='itemDescriptionWrap']/div/p").extract())
            if re.search("Colour: ", description):
                colorName = re.findall(r'[A-Z]\w+', description.split('Colour: ')[1].split('<br>')[0].strip())[0]
                return colorName

    def GetPrice(self, response):
        orignalPrice = response.xpath("//div[@class='itemPriceWrap']//span[contains(@class,'USD')]/text()").get()
        if orignalPrice != None:
            return float(str(orignalPrice).replace('$', '').replace(',', ''))
        else:
            regularPrice = response.xpath(
                "//div[contains(@class,'itemPriceWrap ')]/span[contains(@class,'priceWas')]/span/span[contains(@class,'USD')]/text()").get()

            return float(str(regularPrice).replace('$', '').replace(',', ''))

    def GetSalePrice(self, response):
        salePrice = response.xpath(
            "//div[contains(@class,'itemPriceWrap ')]/span[contains(@class,'priceNow')]/span/span[contains(@class,'USD')]/text()").get()

        if salePrice != None:
            return float(str(salePrice).replace("$", "").replace(',', ''))
        else:
            return 0

    def GetBrand(self, response):
        return str(response.xpath("//div[@class='itemTitle']/h1//strong/a/text()").get()).strip()

    def GetImageUrl(self, response):
        imageUrls = []
        images = response.xpath("//ul[@data-zoom-gallery='itemImage']/li//img/@src").extract()
        for image in images:
            if re.search('smallthumbs', image):
                imageUrls.append(str(image).replace('smallthumbs', 'large'))
        return imageUrls

    def GetDescription(self, response):
        return ' '.join(
            response.xpath("//div[@class='itemDescriptionWrap']/div/p/text()").extract()).replace('\n', '').strip()

    def GetSizes(self, response):
        productSizes = []
        colorName = self.GetSelectedColor(response)
        gender = ProductFilters.objects.get(ProductUrl=GetterSetter.ProductUrl).ParentCategory.split(',')[0]
        sizeOptions = response.xpath(
            "//div[contains(@class,'temSizeSelect')]/div[contains(@class,'inputWrap')]/div/input")
        if sizeOptions:
            for sizeOption in sizeOptions:
                sizeName = str(sizeOption.xpath("./following-sibling::label/text()").get()).strip()
                fitType = GetFitType(gender, sizeName)
                if sizeOption.xpath("./@disabled").get() == 'disabled':
                    available = False
                else:
                    available = True

                sizelist = str(colorName), str(sizeName), available, str(fitType), 0.0, 0.0
                productSizes.append(sizelist)
        else:
            sizeName = 'One Size'
            fitType = GetFitType(gender, sizeName)
            available = True
            sizelist = str(colorName), str(sizeName), available, str(fitType), 0.0, 0.0
            productSizes.append(sizelist)
        return productSizes

    def GetCategory(self, response):
        siteMapCategory = str(Spider_BaseClass.ProductUrlsAndCategory.get(GetterSetter.ProductUrl)).replace('None', '')
        return 'Women ' + siteMapCategory
