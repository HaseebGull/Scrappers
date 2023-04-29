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

import requests


# from requests.adapters import HTTPAdapter
# from requests.packages.urllib3.util.retry import Retry
#
# session = requests.Session()
# retry = Retry(connect=5, backoff_factor=1)
# adapter = HTTPAdapter(max_retries=retry)
# session.mount('http://', adapter)
# session.mount('https://', adapter)

class BloomingdalesScrapper(Spider_BaseClass):
    Spider_BaseClass.cookiesDict = {"currency": "USD"}

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(BloomingdalesScrapper, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        return spider

    def GetProductUrls(self, homePageResponse):
        # ========== Category And Subcategory ==========#
        skipList = ['Casual Pants', 'Chinos', 'Drawstring', 'Sweatpants & Joggers', 'Also Shop: Jeans',
                    "GQ x Bloomingdale's Fit Tips", 'Coats & Jackets', 'Pants, Shorts & Skirts',
                    'Tops, T-Shirts & Shirts', 'Tights & Socks', 'Pants & Shorts', 'T-Shirts & Shirts',
                    'Also Shop: The Vacation Shop', 'Bikini Sets', 'Bikini Tops', 'Bikini Bottoms', 'Tankinis']
        Spider_BaseClass.headersDict = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:96.0) Gecko/20100101 Firefox/96.0",
            # "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5"
        }
        response = requests.get(
            'https://www.bloomingdales.com/xapi/navigate/v1/header?bypass_redirect=yes&viewType=Responsive&currencyCode=USD&_regionCode=US&_navigationType=BROWSE&_shoppingMode=SITE',
            headers=Spider_BaseClass.headersDict, cookies=Spider_BaseClass.cookiesDict)

        homePageJson = json.loads(response.text)
        topNodes = Enumerable(homePageJson['menu']).where(
            lambda x: x['text'] == 'WOMEN' or x['text'] == 'MEN' or x['text'] == 'SALE').to_list()
        # or x['text'] == 'KIDS'
        for topNode in topNodes:
            topcategoryTitle = topNode['text']
            topcategoryUrl = topNode['url']
            print(topcategoryTitle)
            if not topcategoryUrl.startswith(store_url):
                topcategoryUrl = store_url.rstrip('/') + topcategoryUrl
            # ==============================  Category =================================#
            for categoryNodeTokens in topNode['children']:
                for categoryNodeToken in categoryNodeTokens['group']:
                    if 'Clothing' in categoryNodeToken['text'] or 'Girls' == categoryNodeToken['text'] or 'Boys' == \
                            categoryNodeToken['text'] or 'Baby' == \
                            categoryNodeToken['text'] or 'Women' == categoryNodeToken['text']:
                        categoryTitle = categoryNodeToken['text']
                        for subCategoryNodeTokens in categoryNodeToken['children']:
                            for subCategoryNodeToken in subCategoryNodeTokens['group']:
                                if not 'All Dresses' in subCategoryNodeToken['text'] and 'Dress' in \
                                        subCategoryNodeToken['text'] or 'Jumpsuits & Rompers' in \
                                        subCategoryNodeToken['text'] or 'Sleepwear & Robes' in subCategoryNodeToken[
                                    'text'] or 'Swimsuits & Cover-Ups' in subCategoryNodeToken['text'] or \
                                        subCategoryNodeToken['text'] == 'Pants' \
                                        or subCategoryNodeToken['text'] == 'Suits & Tuxedos' or \
                                        'Newborn' in subCategoryNodeToken['text'] \
                                        or 'Baby Girl' in subCategoryNodeToken['text'] or 'Baby Boy' in \
                                        subCategoryNodeToken['text']:

                                    subCategoryTitle = subCategoryNodeToken['text']
                                    subCategorylink = subCategoryNodeToken['url']

                                    if not subCategorylink.startswith(store_url):
                                        subCategorylink = store_url.rstrip('/') + subCategorylink
                                    if subCategoryNodeToken.get('children'):
                                        for subSubCategoryNodeTokens in subCategoryNodeToken['children']:
                                            for subSubCategoryNodeTokens in subSubCategoryNodeTokens['group']:
                                                subSubCategoryTitle = subSubCategoryNodeTokens['text']
                                                subSubCategorylink = subSubCategoryNodeTokens['url']
                                                if not subSubCategorylink.startswith(store_url):
                                                    subSubCategorylink = store_url.rstrip('/') + subSubCategorylink
                                                if subSubCategoryTitle in skipList:
                                                    continue
                                                else:
                                                    category = topcategoryTitle + " " + categoryTitle + " " + subCategoryTitle + " " + subSubCategoryTitle
                                                    self.listing(subSubCategorylink, category)
                                    else:
                                        category = topcategoryTitle + " " + categoryTitle + " " + subCategoryTitle
                                        self.listing(subCategorylink, category)
        return Spider_BaseClass.AllProductUrls

    def listing(self, categorylink, category):
        categoryLinkResponse = session.get(categorylink, headers=Spider_BaseClass.headersDict,
                                           cookies=Spider_BaseClass.cookiesDict, stream=True, timeout=60)
        categoryLinkResponse = HtmlResponse(url=categorylink, body=categoryLinkResponse.text,
                                            encoding='utf-8', headers=Spider_BaseClass.headersDict)
        product_list = categoryLinkResponse.xpath(
            "//ul[@class='items grid-x grid-padding-x']/li/div/a/@href").extract()
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
            nextPageUrl = categoryLinkResponse.xpath("//link[@rel='next']/@href").get()
            if not nextPageUrl.startswith(store_url):
                nextPageUrl = store_url.rstrip('/') + nextPageUrl
            self.listing(nextPageUrl, category)
        except:
            pass

    def GetProducts(self, response):
        global productJson
        ignorProduct = self.IgnoreProduct(response)
        if ignorProduct == True:
            self.ProductIsOutofStock(GetterSetter.ProductUrl)
        else:
            productjsonStr = response.xpath("//script[@data-bootstrap='page/product']/text()").get()
            productJson = json.loads(productjsonStr)
            self.GetProductInfo(response)

    def IgnoreProduct(self, response):
        if re.search('"availability":"', response.text):
            productAvailability = response.text.split('"availability":"')[1].split('"}}')[0].strip()
            if not 'InStock' in productAvailability or 'PreOrder' in productAvailability:
                return True
            else:
                return False

    def GetName(self, response):
        name = productJson['product']['detail']['name']
        return name

    def GetSelectedColor(self, response):
        colorList = []
        global selectedColorID
        colorJToken = productJson['product']['traits']['traitsMaps']['priceToColors']
        for colorObj in colorJToken:
            for id in colorObj['colorIds']:
                colorName = productJson['product']['traits']['colors']['colorMap'][str(id)]['name']
                colorSize = productJson['product']['traits']['colors']['colorMap'][str(id)]['sizes']
                colorList.append((colorName, id, colorSize))
        return colorList
        # selectedColor = productJson['product']['traits']['colors']['colorMap'][str(colorIDs)]['name']
        # return selectedColor

    def GetPrice(self, response):
        orignalPriceList = productJson['product']['pricing']['price']['tieredPrice']
        for orignalPrice in orignalPriceList:
            for price in orignalPrice['values']:
                if price['type'] == 'regular':
                    return float(str(price['formattedValue']).replace('$', '').replace(',', '').replace('USD', ''))

    def GetSalePrice(self, response):
        salePrice = ''
        salePriceList = productJson['product']['pricing']['price']['tieredPrice']
        for salePriceJToken in salePriceList:
            for price in salePriceJToken['values']:
                if price['type'] == 'discount':
                    salePrice = float(str(price['formattedValue']).replace('$', '').replace(',', '').replace('USD', ''))
        if salePrice:
            return salePrice
        else:
            return 0

    def GetBrand(self, response):
        return productJson['product']['detail']['brand']['name']

    def GetImageUrl(self, response):
        imageUrls = []
        imagesStartingUrl = productJson['product']['urlTemplate']['product']
        imagesJToken = productJson['product']['imagery']['images']
        for image in imagesJToken:
            imageUrls.append(imagesStartingUrl + image['filePath'])
        return imageUrls

    def GetDescription(self, response):
        descriptionList = []
        materialList = []
        detail = productJson['product']['detail']
        if detail.get('bulletText'):
            descriptionJToken = productJson['product']['detail']['bulletText']
            for desc in descriptionJToken:
                descriptionList.append(desc)
            description = ' , '.join(descriptionList)
        else:
            description = detail.get('description')
        if detail.get('materialsAndCare'):
            materialsJToken = productJson['product']['detail']['materialsAndCare']
            for mat in materialsJToken:
                materialList.append(mat)
            material = ','.join(materialList)
        else:
            material = ''
        return description + material

    def GetSizes(self, response):
        productSizes = []
        color = self.GetSelectedColor(response)
        print(color)
        gender = ProductFilters.objects.get(ProductUrl=GetterSetter.ProductUrl).ParentCategory.split(',')[0]
        sizeJToken = productJson['product']['traits']['sizes']['sizeMap']
        for sizeSequance in color:
            for size in sizeSequance[2]:
                if sizeSequance[1] in sizeJToken[str(size)]['colors']:
                    sizeName = sizeJToken[str(size)]['name']
                    colorName = sizeSequance[0]
                    available = True
                    fitType = GetFitType(gender, str(sizeName).strip())
                    sizelist = str(colorName), str(sizeName), available, str(fitType), 0.0, 0.0
                    productSizes.append(sizelist)
        return productSizes

    def GetCategory(self, response):
        siteMapCategory = str(Spider_BaseClass.ProductUrlsAndCategory.get(GetterSetter.ProductUrl)).replace('None', '')
        return 'Men ' + siteMapCategory
