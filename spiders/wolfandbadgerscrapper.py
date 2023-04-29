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


class WolfandbadgerScrapper(Spider_BaseClass):
    Spider_BaseClass.cookiesDict = {"currency": "USD", "currencyOverride": "USD"}
    Spider_BaseClass.testingGender = 'Women'

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(WolfandbadgerScrapper, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        return spider

    def GetProductUrls(self, homePageResponse):
        # ========== Category And Subcategory ==========#
        topCategoryNodes = homePageResponse.xpath(
            "//div[contains(@class,'Header__MiddleColumn')]/div/div[a[contains(div/text(),'Women') or contains(div/text(),'Men')]]")
        for topCategoryNode in topCategoryNodes:
            topCategoryTitle = topCategoryNode.xpath("./a/div/text()").get().strip()
            topCategorylink = topCategoryNode.xpath("./a/@href").get()
            if not topCategorylink.startswith(store_url):
                topCategorylink = store_url.rstrip('/') + topCategorylink
            categoryNodes = topCategoryNode.xpath(
                "./div/div//ul[li/a[contains(text(),'Clothing')]]")
            for categoryNode in categoryNodes:
                categoryTitle = categoryNode.xpath("./li/a/text()").get().strip()
                categorylink = categoryNode.xpath("./li/a/@href").get()
                if not categorylink.startswith(store_url):
                    categorylink = store_url.rstrip('/') + categorylink
                subCategoryNodes = categoryNode.xpath(
                    "./li/following-sibling::li/a[contains(text(),'Dress') or contains(text(),'Jumpsuits')]")
                for subCategoryNode in subCategoryNodes:
                    subCategoryTitle = subCategoryNode.xpath("./text()").get().strip()
                    subCategorylink = subCategoryNode.xpath("./@href").get()
                    if not subCategorylink.startswith(store_url):
                        subCategorylink = store_url.rstrip('/') + subCategorylink
                    category = topCategoryTitle + " " + categoryTitle + " " + subCategoryTitle
                    self.listing(subCategorylink, category)
        return Spider_BaseClass.AllProductUrls

    def listing(self, categorylink, category):
        # ALGOLIA_INDEX_NAME = getenv('live_product_index_categories')
        # client = SearchClient.create('FA5YXNYRL9', '0a3252e3bf0cf387962a8f6e4159b665')
        # index = client.init_index(ALGOLIA_INDEX_NAME)
        # index.set_settings({
        #     'paginationLimitedTo': 7000,
        #     'hitsPerPage': 100
        #
        # })
        category = str(category).split(' ')
        apiUrl = 'https://xo4u4y7c0t-dsn.algolia.net/1/indexes/*/queries?x-algolia-agent=Algolia%20for%20JavaScript%20(4.8.3)%3B%20Browser%20(lite)%3B%20react%20(17.0.1)%3B%20react-instantsearch%20(6.8.2)%3B%20JS%20Helper%20(3.3.2)&x-algolia-api-key=bb6097513c7231e0779e90db875b7563&x-algolia-application-id=XO4U4Y7C0T'
        body = """{"requests":[{"indexName":"live_product_index_categories","params":"highlightPreTag=%3Cais-highlight-0000000000%3E&highlightPostTag=%3C%2Fais-highlight-0000000000%3E&clickAnalytics=true&attributesToRetrieve=%5B%22id%22%2C%22absolute_url%22%2C%22name%22%2C%22parent_name%22%2C%22designer_name%22%2C%22designer_url%22%2C%22main_image_picture%22%2C%22alt_image_picture%22%2C%22algolia_zoned_sale_prices%22%2C%22algolia_zoned_unit_prices%22%2C%22algolia_on_sale%22%2C%22algolia_is_available%22%2C%22slug%22%5D&ruleContexts=%5B%22category_""" + \
               category[0].lower() + """_""" + category[1].lower() + """_""" + category[
                   2].lower() + """%22%2C%22locale_us%22%5D&filters=algolia_hierarchical_categories.lvl2%3A'""" + \
               category[0] + """%20%2F%20""" + category[1] + """%20%2F%20""" + category[
                   2] + """'%20AND%20algolia_approved_timestamp%20%3C%201646711620&analytics=true&enableRules=true&maxValuesPerFacet=999&page=0&facets=%5B%22algolia_style%22%2C%22algolia_color%22%2C%22algolia_material%22%2C%22algolia_zoned_sale_prices.us.USD%22%2C%22algolia_size%22%2C%22algolia_designer_sustainability_statuses%22%2C%22designer%22%2C%22algolia_stock_location%22%2C%22available_in_store_locations%22%5D&tagFilters="}]}"""

        responeapi = requests.post(url=apiUrl, data=body, timeout=6000)
        apiresponse = json.loads(responeapi.content)
        totalProducts = apiresponse['results'][0]['nbHits']
        pageNo = apiresponse['results'][0]['page']
        totalPages = apiresponse['results'][0]['nbPages']
        if totalProducts % 60 == 0:
            totalPages = totalProducts / 60
        else:
            totalPages = totalProducts / 60 + 1

            while pageNo <= totalPages:
                pageNo += 1
                for apiproducturl in apiresponse['results'][0]['hits']:
                    try:
                        style = apiproducturl['_highlightResult']['algolia_style'][0]['value']
                    except:
                        style = ''

                    productUrl = store_url.rstrip('/') + apiproducturl['absolute_url']
                    print("PRODUCT URL :", productUrl)
                    Spider_BaseClass.AllProductUrls.append(productUrl)
                    try:
                        filterCategory = Spider_BaseClass.ProductUrlsAndCategory[productUrl]
                        if filterCategory:
                            filterCategory = filterCategory + " " + ' '.join(category) + " " + style
                            Spider_BaseClass.ProductUrlsAndCategory[productUrl] = filterCategory
                    except:
                        Spider_BaseClass.ProductUrlsAndCategory[productUrl] = ' '.join(category) + " " + style
            try:
                apiUrl = 'https://xo4u4y7c0t-dsn.algolia.net/1/indexes/*/queries?x-algolia-agent=Algolia%20for%20JavaScript%20(4.8.3)%3B%20Browser%20(lite)%3B%20react%20(17.0.1)%3B%20react-instantsearch%20(6.8.2)%3B%20JS%20Helper%20(3.3.2)&x-algolia-api-key=bb6097513c7231e0779e90db875b7563&x-algolia-application-id=XO4U4Y7C0T'
                body = """{"requests":[{"indexName":"live_product_index_categories","params":"highlightPreTag=%3Cais-highlight-0000000000%3E&highlightPostTag=%3C%2Fais-highlight-0000000000%3E&clickAnalytics=true&attributesToRetrieve=%5B%22id%22%2C%22absolute_url%22%2C%22name%22%2C%22parent_name%22%2C%22designer_name%22%2C%22designer_url%22%2C%22main_image_picture%22%2C%22alt_image_picture%22%2C%22algolia_zoned_sale_prices%22%2C%22algolia_zoned_unit_prices%22%2C%22algolia_on_sale%22%2C%22algolia_is_available%22%2C%22slug%22%5D&ruleContexts=%5B%22category_""" + \
                       category[0].lower() + """_""" + category[1].lower() + """_""" + category[
                           2].lower() + """%22%2C%22locale_us%22%5D&filters=algolia_hierarchical_categories.lvl2%3A'""" + \
                       category[0] + """%20%2F%20""" + category[1] + """%20%2F%20""" + category[
                           2] + """'%20AND%20algolia_approved_timestamp%20%3C%201646711620&analytics=true&enableRules=true&maxValuesPerFacet=999&page=""" + str(
                    pageNo) + """"&facets=%5B%22algolia_style%22%2C%22algolia_color%22%2C%22algolia_material%22%2C%22algolia_zoned_sale_prices.us.USD%22%2C%22algolia_size%22%2C%22algolia_designer_sustainability_statuses%22%2C%22designer%22%2C%22algolia_stock_location%22%2C%22available_in_store_locations%22%5D&tagFilters="}]}"""

                responeapi = requests.post(url=apiUrl, data=body, timeout=6000)
                apiresponse = json.loads(responeapi.content)
            except:
                pass

    def GetProducts(self, response):
        global productjson

        ignorProduct = self.IgnoreProduct(response)
        if ignorProduct == True:
            self.ProductIsOutofStock(GetterSetter.ProductUrl)
        else:
            product_url = GetterSetter.ProductUrl
            jstr = str(product_url).split('us')
            apiJsonUrl = jstr[0] + "us/page-data" + jstr[1] + "page-data.json"
            apiResponse = requests.get(apiJsonUrl)
            productjson = json.loads(apiResponse.content)

            sizeApi = 'https://www.wolfandbadger.com/api/v1/products/' + str(
                productjson['result']['pageContext']['id']) + '/?language_code=en-us'
            sizeApiResponse = requests.get(sizeApi)
            global sizeJson
            sizeJson = json.loads(sizeApiResponse.content)
            self.GetProductInfo(response)

    def IgnoreProduct(self, response):
        if re.search('"availability":"', response.text):
            productAvailability = response.text.split('"availability":"')[1].split('"}}')[0].strip()
            if not 'InStock' in productAvailability or 'PreOrder' in productAvailability:
                return True
            else:
                return False

    def GetName(self, response):
        color = self.GetSelectedColor()
        name = productjson['result']['pageContext']['title']
        if not color == '' and not re.search(color, name, re.I):
            name = name + " - " + color
        return name

    def GetSelectedColor(self):
        return productjson['result']['pageContext']['color']

    def GetPrice(self, response):
        orignalPrice = sizeJson['price']
        if orignalPrice != None:
            return float(str(orignalPrice).replace('$', '').replace(',', ''))
        # else:
        #     regularPrice = response.xpath(
        #         "//div[@id='salePriceContainer']/s[@id='retailPriceStrikethrough']/text()").get()
        #     return float(str(regularPrice).replace('$', '').replace(',', ''))

    def GetSalePrice(self, response):
        salePrice = sizeJson['salePrice']
        if salePrice != None:
            return float(str(salePrice).replace("$", "").replace(',', ''))
        else:
            return 0

    def GetBrand(self, response):
        return productjson['result']['pageContext']['brand']['title']

    def GetImageUrl(self, response):
        imageUrls = []
        for image in productjson['result']['pageContext']['images']:
            imageUrls.append(
                'https://res.cloudinary.com/wolfandbadger/image/upload/f_auto,q_auto:best,c_pad,h_1200,w_1200/' + image[
                    'image'])
        return imageUrls

    def GetDescription(self, response):
        description = productjson['result']['pageContext']['description']

        careInfo = productjson['result']['pageContext']['careInfo']
        return description + careInfo

    def GetSizes(self, response):
        productSizes = []
        colorName = self.GetSelectedColor()
        gender = ProductFilters.objects.get(ProductUrl=GetterSetter.ProductUrl).ParentCategory.split(',')[0]
        for sizeJtoken in sizeJson['sizes']:
            if sizeJtoken['stock'] != 0:
                sizeName = sizeJtoken['title']
                available = True
                fitType = GetFitType(gender, sizeName)
                sizelist = str(colorName), str(sizeName), available, str(fitType), 0.0, 0.0
                productSizes.append(sizelist)
        return productSizes

    def GetCategory(self, response):
        siteMapCategory = str(Spider_BaseClass.ProductUrlsAndCategory.get(GetterSetter.ProductUrl)).replace('None', '')
        return 'Women ' + siteMapCategory + productjson['result']['pageContext']['style'] + \
               productjson['result']['pageContext'][
                   'material']
