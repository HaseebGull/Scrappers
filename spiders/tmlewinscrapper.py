import re
import sys, json
from pathlib import Path
from SiteSizesDict import *

DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(DIR.parent.parent.parent.parent))
__package__ = DIR.name

import django

django.setup()
from BaseClass import *
from scrapy import signals

store_url = sys.argv[4]

class TmlewinScrapper(Spider_BaseClass):
    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(TmlewinScrapper, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        return spider

    def GetProductUrls(self, homePageResponse):
        # ========== Category And Subcategory ==========#
        homepage_json = json.loads(
            homePageResponse.xpath("//script[@id='__NEXT_DATA__' and @type='application/json']/text()").get().strip())
        topCategoryNodes = homepage_json['props']['pageProps']['initialReduxState']['menu']['0']['menu_items']
        for topCategoryNode in topCategoryNodes:
            if topCategoryNode['title'] == 'Suits' or topCategoryNode['title'] == 'SALE':
                topCategoryTitle = topCategoryNode['title']
                topCategorylink = topCategoryNode['canonical_path']
                if not topCategorylink.startswith(store_url):
                    topCategorylink = store_url.rstrip('/') + topCategorylink
                print("TOP CATEGORY  :", topCategoryTitle, "TOP CATEGORY LINK  :", topCategorylink)
                for categoryNodes in topCategoryNode['menu_items']:
                    for subCategoryNode in categoryNodes['menu_items']:
                        if ((categoryNodes['title'] == "Style" or categoryNodes['title'] == "Collection") and (
                                'jackets' not in subCategoryNode['title'].lower() and 'coats' not in subCategoryNode[
                            'title'].lower() and 'trousers' not in subCategoryNode['title'].lower() and 'tuxedos' not in
                                subCategoryNode['title'].lower())) or ((
                                "Shop Sale" == categoryNodes['title'].strip() and 'sale suits' == subCategoryNode[
                            'title'].lower().strip())):
                            print('subCategoryNode:', subCategoryNode)
                            subCategoryTitle = subCategoryNode['title']
                            subCategorylink = subCategoryNode['canonical_path'].strip()
                            if not subCategorylink.startswith(store_url):
                                subCategorylink = store_url.rstrip('/') + subCategorylink
                            print("SUB CATEGORY  :", subCategoryTitle, "SUB CATEGORY LINK  :", subCategorylink)
                            if re.search('\?', subCategorylink):
                                subCategorylink = 'https' + subCategorylink.split('https' or 'http')[1].split('?')[
                                    0].strip()
                            category = topCategoryTitle + " " + subCategoryTitle + " " + subCategoryTitle
                            self.listing(subCategorylink, category)
                            # break
        return Spider_BaseClass.AllProductUrls

    def ProductListJsonFromPageSource(self, subCategorylink):
        subCategoryLinkResponse = requests.get(subCategorylink)
        subCategoryLinkResponse = HtmlResponse(url=subCategorylink, body=subCategoryLinkResponse.text, encoding='utf-8')
        homepage_json = json.loads(
            subCategoryLinkResponse.xpath("//script[@id='__NEXT_DATA__' and @type='application/json']/text()").get().strip())
        product_list = homepage_json['props']['pageProps']
        return product_list

    def listing(self, subCategorylink, category):
        product_list = self.ProductListJsonFromPageSource(subCategorylink)
        subCategorylink = subCategorylink + '?size=' + str(
            int(product_list['resultsState']['rawResults'][0]['hitsPerPage']) * int(
                product_list['resultsState']['rawResults'][0]['nbPages']))
        product_list = self.ProductListJsonFromPageSource(subCategorylink)
        product_list = product_list['resultsState']['rawResults'][0]['hits']
        print('len of product_list', len(product_list))
        for product in product_list:
            productUrl = product['product_path']
            if not productUrl.startswith(store_url):
                productUrl = store_url.rstrip('/') + productUrl
            Spider_BaseClass.AllProductUrls.append(productUrl)
            siteMapCategory = str(Spider_BaseClass.ProductUrlsAndCategory.get(productUrl)).replace('None', '')
            if siteMapCategory:
                Spider_BaseClass.ProductUrlsAndCategory[productUrl] = siteMapCategory + " " + category
            else:
                Spider_BaseClass.ProductUrlsAndCategory[productUrl] = category

    def GetProducts(self, response):
        global productJson
        productJson = json.loads(
            response.xpath("//script[@id='__NEXT_DATA__' and @type='application/json']/text()").get().strip())
        productJson = productJson['props']['pageProps']['initialReduxState']['product']

        ignorProduct = self.IgnoreProduct(response)
        if ignorProduct == True:
            self.ProductIsOutofStock(GetterSetter.ProductUrl)
        else:
            self.GetProductInfo(response)

    def IgnoreProduct(self, response):
        if str(productJson['available_to_browse']).lower() == 'false':
            return True
        else:
            return False

    def GetName(self, response):
        return productJson['title']

    def GetPrice(self, response):
        originalPrice = response.xpath("//p[contains(@class,'priceHolder')]//span[contains(@class,'sale_original')]")
        if originalPrice:
            return float(str(originalPrice.xpath("./text()").get().strip()).replace('$', '').replace(',', ''))
        else:
            return float(str(response.xpath(
                "//p[contains(@class,'priceHolder')]//span[contains(@class,'individual_standard')]/text()").get().strip()).replace(
                '$', '').replace(',', ''))

    def GetSalePrice(self, response):
        salePrice = response.xpath("//p[contains(@class,'priceHolder')]//span[contains(@class,'sale_discount')]")
        if salePrice:
            return float(str(salePrice.xpath("./text()").get().strip()).replace('$', '').replace(',', ''))
        else:
            return 0

    def GetBrand(self, response):
        return 'T.M.Lewin'

    def GetImageUrl(self, response):
        imageUrls = []
        images = productJson['asset_files']
        for image in images:
            imageUrls.append(image['s3_url'])
        return imageUrls

    def GetDescription(self, response):
        return productJson['description']

    def GetSizes(self, response):
        bodyFit = ''
        colorName = ''
        productSizes = []

        colorDict = Enumerable(productJson['dimensions']).where(lambda x: x['key'] == 'colour').first_or_default()
        if colorDict:
            for prodAttribute in colorDict['options']:
                if str(prodAttribute['productUrl']) in str(GetterSetter.ProductUrl):
                    colorName = prodAttribute['value']
                    break

        bodyFitDict = Enumerable(productJson['dimensions']).where(lambda x: x['key'] == 'fit').first_or_default()
        if bodyFitDict:
            for prodAttribute in bodyFitDict['options']:
                if str(prodAttribute['productUrl']) in str(GetterSetter.ProductUrl):
                    bodyFit = prodAttribute['value']
                    break

        variantList = Enumerable(productJson['dimensions']).where(lambda x: x['type'] == 'variant').select(
            lambda y: y['key']).to_list()

        for size in productJson['variants']:
            if len(variantList) > 1:
                casualSize = Enumerable(variantList).where(lambda x: x == 'casualSize').first_or_default()
                if casualSize == '' or casualSize is None:
                    sizeName = size['meta_attributes'][variantList[0]]['value'] + ' - ' + \
                               size['meta_attributes'][variantList[1]]['value']
                    fitType = 'Regular'
                else:
                    sizeAttribute = Enumerable(variantList).where(lambda x: x != 'casualSize').first_or_default()
                    sizeName = size['meta_attributes'][sizeAttribute]['value']
                    fitType = size['meta_attributes'][casualSize]['value']
            else:
                sizeName = size['meta_attributes'][variantList[0]]['value']
                fitType = 'Regular'

            available = size['available_to_order']

            sizeList = str(colorName).title(), str(sizeName), available, str(fitType), 0, 0, str(bodyFit)
            productSizes.append(sizeList)

        print('productSizes:', productSizes)
        return productSizes

    def GetCategory(self, response):
        filterList = []
        if GetterSetter.ProductUrl in Spider_BaseClass.ProductUrlsAndCategory:
            categories = Spider_BaseClass.ProductUrlsAndCategory[GetterSetter.ProductUrl]
            for category in str(categories).split('$'):
                filterList.append(category)

        for proAttributeToken in productJson['meta_attributes']:
            attributeValue = productJson['meta_attributes'][proAttributeToken]['value']
            filterList.append(attributeValue)

        filters = '$'.join(set(filterList)) + '$'
        return "Men " + filters
