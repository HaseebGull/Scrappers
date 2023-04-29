import json
import sys
from pathlib import Path

import requests

DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(DIR.parent.parent.parent.parent))
__package__ = DIR.name

import django

django.setup()
from BaseClass import *
from scrapy import signals

store_url = sys.argv[4]
session = requests.Session()
retry = Retry(total=5, connect=5, backoff_factor=1)
adapter = HTTPAdapter(max_retries=retry)
session.mount('http://', adapter)
session.mount('https://', adapter)


class boohooScrapper(Spider_BaseClass):
    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(boohooScrapper, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        return spider

    def GetProductUrls(self, homePageResponse):
        # ========== Category And Subcategory ==========#
        genderNodes = homePageResponse.xpath(
            "//div[@class='b-menu_bar-tabs']/a[contains(text(),'WOMENS')]")
        for genderNode in genderNodes:
            gendertitle = genderNode.xpath("./text()").get().strip()
            genderLink = genderNode.xpath("./@href").get().strip()
            InnerBar = genderNode.xpath("./@data-panel-name").get().strip()
            if not genderLink.startswith(store_url):
                genderLink = store_url.rstrip('/') + genderLink
            topCategoryNodes = homePageResponse.xpath(
                "//div[@id='" + str(
                    InnerBar) + "']/div/ul[@class='b-menu_bar-inner']/li[a[not(contains(text(),'SHOES')) and not("
                                "contains(text(),'BEAUTY')) and not(contains(text(),'SUSTAINABILITY'))]]")
            for topCategoryNode in topCategoryNodes:
                topCategoryTitle = topCategoryNode.xpath("./a/text()").get().strip()
                categoryNodes = topCategoryNode.xpath(
                    "./div/div/div/div[a]")
                for categoryNode in categoryNodes:
                    subCategoryNodes = categoryNode.xpath(
                        "./div/div/a[not(contains(text(),'All')) and contains(text(),'Dress') or contains(text(),"
                        "'Jumpsuit') or contains(text(),'Rompers') or contains(text(),'Suit') or contains(text(),"
                        "'Sets') or contains(text(),'Sleep') or contains(text(),'Swim') or contains(text(),"
                        "'Track') or contains(text(),'Co-ords') or contains(text(),'Outfits') and not(contains(text("
                        "),'All Spring Outfits')) and not(contains(text(),'Spring Break')) or contains(text(),"
                        "'Bodysuits')]")
                    for subCategoryNode in subCategoryNodes:
                        subCategoryTitle = subCategoryNode.xpath("./text()").get().strip()
                        subCategorylink = subCategoryNode.xpath("./@href").get()
                        if not subCategorylink.startswith(store_url):
                            subCategorylink = store_url.rstrip('/') + subCategorylink
                        category = gendertitle + " " + topCategoryTitle + " " + subCategoryTitle
                        self.listing(subCategorylink, category)
        return Spider_BaseClass.AllProductUrls

    def listing(self, categorylink, category):
        CategoryLinkResponse = session.get(categorylink, stream=True)
        categoryPageResponse = HtmlResponse(url=categorylink, body=CategoryLinkResponse.text, encoding='utf-8')
        product_list = categoryPageResponse.xpath(
            "//h3[@class='b-product_tile-title']/a/@href").extract()
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
            nextpageUrl = \
                categoryPageResponse.xpath("//link[@rel='next']/@href").get()
            if not nextpageUrl.startswith(store_url):
                nextpageUrl = store_url.rstrip('/') + nextpageUrl
            self.listing(nextpageUrl, category)
        except:
            pass

    def GetProducts(self, response):
        global productjson
        ignorProduct = self.IgnoreProduct(response)
        if ignorProduct == True:
            self.ProductIsOutofStock(GetterSetter.ProductUrl)
        else:
            category = self.GetCategory(response)
            name = self.GetName(response)
            if (re.search('Two Piece Sets', category, re.IGNORECASE) or
                re.search('wear', category, re.IGNORECASE) or
                re.search('Outfits', category, re.IGNORECASE) or
                re.search('Suits & Tailoring', category, re.IGNORECASE)) and not re.search(
                r'\b((shirt(dress?)|jump(suit?)|dress|gown|suit|co-ord|romper|set|swimwear|sleepwear|caftan)(s|es)?)\b',
                name, re.IGNORECASE):
                print('Skipping Non Dress Product')
                self.ProductIsOutofStock(GetterSetter.ProductUrl)
            else:
                self.GetProductInfo(response)

    def IgnoreProduct(self, response):
        if re.search('"availability":', response.text):
            productAvailability = response.text.split('"availability":')[1].split(',')[0].strip()
            if not 'InStock' in productAvailability:
                return True
            else:
                return False

    def GetName(self, response):
        return response.xpath("//h1[@class='b-product_details-name']/text()").get()

    def GetSelectedColor(self, response):
        return response.xpath(
            "//div[@data-id='attr-line-color' and contains(span/text(),'Colour')]/span[@class='b-variation_label-value']/text()").get().strip()

    def GetPrice(self, response):
        orignalPrice = response.xpath(
            "//div[@class='b-product_details-price']/div/span[@class='b-price-item ']/text()").get()
        if orignalPrice != None:
            return float(str(orignalPrice).replace('$', '').replace(',', ''))
        else:
            regularPrice = response.xpath(
                "//div[@class='b-product_details-price']/div/span[contains(@class,'old')]/text()").get()
            return float(str(regularPrice).replace('$', '').replace(',', ''))

    def GetSalePrice(self, response):
        salePrice = response.xpath(
            "//div[@class='b-product_details-price']/div/span[contains(@class,'new')]/text()").get()
        if salePrice != None:
            return float(str(salePrice).replace("$", "").replace(',', ''))
        else:
            return 0

    def GetBrand(self, response):
        return 'boohoo'

    def GetImageUrl(self, response):
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:100.0) Gecko/20100101 Firefox/100.0'}
        imageList = []
        try:
            image = response.xpath("//div[@id='product_gallery_track']/div/picture/img/@data-original-src").get()
            imageUrl = 'https:' + str(image).rstrip('?qlt=80&fmt=auto').rstrip('/'). \
                replace('/i/', '/s/').replace('_xl', '_ms') + '.js'

            imageUrlResp = requests.get(imageUrl, headers=headers)
            imageJsonStr = imageUrlResp.text.lstrip('imgSet(').rstrip(');')
            imageJson = json.loads(imageJsonStr)
            for image in imageJson['items']:
                imageList.append(image['src'])
            return imageList
        except:
            images = response.xpath("//div[@id='product_gallery_track']/div/picture/img/@data-original-src").extract()
            for image in images:
                imageList.append(image)
            return imageList

    def GetDescription(self, response):
        return ' '.join(response.xpath("//div[@data-id='descriptions']/div/p/text()").extract())

    def GetSizes(self, response):
        productSizes = []
        colorNodes = response.xpath("(//div[@aria-label='Colour'])[1]/button[not(contains(@class,'disabled'))]")
        if colorNodes and len(colorNodes) > 1:
            for color in colorNodes:
                colorID = color.xpath("./@data-attr-value").get()
                colorName = color.xpath("./@title").get().strip().replace("Colour: ", "")

                productUrlWithColor = GetterSetter.ProductUrl + "?color=" + colorID
                productUrlWithColorResponse = session.get(productUrlWithColor)
                productUrlWithColorResponse = HtmlResponse(url=productUrlWithColor,
                                                           body=productUrlWithColorResponse.text, encoding='utf-8')

                gender = ProductFilters.objects.get(ProductUrl=GetterSetter.ProductUrl).ParentCategory.split(',')[0]

                sizeOptions = productUrlWithColorResponse.xpath(
                    "//div[@class='b-product_details-form']//section[@class='b-variations_item m-swatch m-size']/div/div/button[not(contains(@class,'disabled'))]/span/span/text()").extract()
                for sizeName in sizeOptions:
                    available = True
                    fitType = GetFitType(gender, sizeName)
                    sizelist = str(colorName), str(sizeName), available, str(fitType), 0.0, 0.0
                    productSizes.append(sizelist)
        else:
            gender = ProductFilters.objects.get(ProductUrl=GetterSetter.ProductUrl).ParentCategory.split(',')[0]

            sizeOptions = response.xpath(
                "//div[@class='b-product_details-form']//section[@class='b-variations_item m-swatch m-size']/div/div/button[not(contains(@class,'disabled'))]/span/span/text()").extract()
            for sizeName in sizeOptions:
                available = True
                fitType = GetFitType(gender, sizeName)
                colorName = colorNodes.xpath("./@title").get().strip().replace("Colour: ", "")
                sizelist = str(colorName), str(sizeName), available, str(fitType), 0.0, 0.0
                productSizes.append(sizelist)
        return productSizes

    def GetCategory(self, response):
        siteMapCategory = str(Spider_BaseClass.ProductUrlsAndCategory.get(GetterSetter.ProductUrl)).replace('None', '')
        return siteMapCategory.strip()
