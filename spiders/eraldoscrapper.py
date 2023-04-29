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


class EraldoScrapper(Spider_BaseClass):
    Spider_BaseClass.cookies_dict = {"cart_currency": "USD"}

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(EraldoScrapper, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        return spider

    def GetProductUrls(self, homePageResponse):
        global homePageJson
        if re.search('window.__PRELOADED_STATE__ = ', homePageResponse.text):
            homePageJson = homePageResponse.text.split('window.__PRELOADED_STATE__ = ')[1].split('</script>')[
                0].strip()
        homePageJson = json.loads(homePageJson)
        # ============================== TOP CATEGORY =================================#
        for topNodes in homePageJson['navigation']['main']['content']:
            if 'Men' in topNodes['title'] or 'Women ' in topNodes['title'] or 'Sale ' in topNodes['title']:
                topcategoryTitle = topNodes['title']
                topcategoryLink = topNodes['link']['url']
                if not topcategoryLink.startswith(store_url):
                    topcategoryLink = store_url.rstrip('/') + topcategoryLink
                print('TOP CATEGORY TITLE :', topcategoryTitle)
                print('TOP CATEGORY LINK :', topcategoryLink)

                # ============================== Category =================================#
                if topNodes['children'] and Enumerable(topNodes['children']).where(
                        lambda x: x['title'] == 'New In' or x['title'] == 'Clothing' or x[
                            'title'] == 'Men' or x['title'] == 'Women').to_list():

                    categoryTokens = Enumerable(topNodes['children']).where(
                        lambda x: x['title'] == 'Clothing' or x['title'] == 'New In'
                                  or x['title'] == 'Men'
                                  or x['title'] == 'Women').to_list()
                    for categoryNode in categoryTokens:
                        categoryNodeTitle = categoryNode['title']
                        print('CATEGORY TITLE :', categoryNodeTitle)

                        # ============================== SUB Category =================================#
                        subCategoryTokens = Enumerable(categoryNode['children']).where(
                            lambda x: x['title'] == 'Dresses' or x['title'] == 'Clothing' or x[
                                'title'] == 'Dresses').to_list()
                        if subCategoryTokens:
                            for subCategoryNode in subCategoryTokens:

                                subCategoryNodeTitle = subCategoryNode['title']
                                subCategoryNodeLink = subCategoryNode['link']['url']
                                if not subCategoryNodeLink.startswith(store_url):
                                    subCategoryNodeLink = store_url.rstrip('/') + subCategoryNodeLink
                                print('SUB CATEGORY TITLE :', subCategoryNodeTitle)
                                print('SUB CATEGORY LINK :', subCategoryNodeLink)
                                self.listing(subCategoryNodeLink, subCategoryNodeTitle)
                        else:
                            if categoryNode['link']['url'] == None:
                                continue
                            else:
                                categoryNodeLink = categoryNode['link']['url']
                                if not categoryNodeLink.startswith(store_url):
                                    categoryNodeLink = store_url.rstrip('/') + categoryNodeLink
                                self.listing(categoryNodeLink, categoryNodeTitle)
                    else:
                        if not str(topcategoryLink).startswith(store_url):
                            topcategoryLink = store_url.rstrip('/') + topcategoryLink
                        self.listing(topcategoryLink, topcategoryTitle)
        return Spider_BaseClass.AllProductUrls

    def listing(self, categorylink, category):
        global CategoryPageJson
        CategoryLinkResponse = requests.get(categorylink)
        CategoryLinkResponse = HtmlResponse(url=categorylink, body=CategoryLinkResponse.text, encoding='utf-8')
        if re.search('window.__PRELOADED_STATE__ = ', CategoryLinkResponse.text):
            CategoryPageJson = CategoryLinkResponse.text.split('window.__PRELOADED_STATE__ = ')[1].split('</script>')[
                0].strip()
        CategoryPageJson = json.loads(CategoryPageJson)
        key = Enumerable(CategoryPageJson['products']['listings'].keys()).select(lambda x: x).first_or_default()
        for productJTOKEN in CategoryPageJson['products']['listings'][key]['result']['entries']:
            productUrl = '/shopping/' + productJTOKEN['slug']
            if not productUrl.startswith(store_url):
                productUrl = store_url.rstrip('/') + productUrl
            print('Product Url: ', productUrl)
            Spider_BaseClass.AllProductUrls.append(productUrl)
            siteMapCategory = str(Spider_BaseClass.ProductUrlsAndCategory.get(productUrl)).replace('None', '')
            if siteMapCategory:
                Spider_BaseClass.ProductUrlsAndCategory[productUrl] = siteMapCategory + " " + category
            else:
                Spider_BaseClass.ProductUrlsAndCategory[productUrl] = category
        # try:
        #     nextPageUrl = CategoryLinkResponse.xpath("//link[@rel='next']/@href").extract()[0]
        #     print('nextPageUrl:', nextPageUrl)
        #     if not nextPageUrl.startswith(store_url):
        #         nextPageUrl = store_url.rstrip('/') + nextPageUrl
        #     self.listing(nextPageUrl, category)
        # except:
        #     pass

    def GetProducts(self, response):
        global productjson
        if re.search('window.__PRELOADED_STATE__ = ', response.text):
            productjson = response.text.split('window.__PRELOADED_STATE__ = ')[1].split('</script>')[
                0].strip()
        productjson = json.loads(productjson)

        ignorProduct = self.IgnoreProduct(response)
        if ignorProduct == True:
            pass
        else:
            self.GetProductInfo(response)

    def GetName(self, response):
        global productID
        productID = Enumerable(productjson['products']['details'].keys()).select(lambda x: x).first_or_default()
        color = self.getcolor()
        name = productjson['products']['details'][productID]['product']['name']
        if not color == '' and not re.search(color, name):
            name = name + " - " + color
        return name

    def GetPrice(self, response):
        orignalPrice = productjson['products']['details'][productID]['product']['price']['formatted'][
            'includingTaxesWithoutDiscount']
        if orignalPrice != None:
            return float(str(orignalPrice).replace('$', '').replace(',', ''))
        else:
            regularPrice = productjson['products']['details'][productID]['product']['price']['formatted'][
                'includingTaxes']
            return float(str(regularPrice).replace('$', '').replace(',', ''))

    def GetSalePrice(self, response):
        salePrice = productjson['products']['details'][productID]['product']['price']['formatted']['includingTaxes']
        if salePrice != None:
            return float(str(salePrice).replace("$", "").replace(',', ''))
        else:
            return 0

    def GetBrand(self, response):
        return productjson['products']['details'][productID]['product']['brand']['name']

    def GetImageUrl(self, response):
        imageUrls = []
        for imageJTOKEN in productjson['products']['details'][productID]['product']['resources']['details']:
            imageurl = imageJTOKEN['sources']['2048']
            imageUrls.append(imageurl)
        return imageUrls

    def GetDescription(self, response):

        description = productjson['products']['details'][productID]['product']['description']['full']
        if description:
            return description
        else:
            descriptionJToken = productjson['products']['details'][productID]['product']['information']
            for description in descriptionJToken:
                if description['title'] == 'Description':
                    return description['value']

    def GetSizes(self, response):
        productSizes = []
        for sizeJTOKEN in productjson['products']['details'][productID]['product']['sizes']:
            size = sizeJTOKEN['name']
            available = True
            colorName = self.getcolor()
            sizelist = str(colorName), str(size), available, 0.0, 0.0
            productSizes.append(sizelist)
        return productSizes

    def getcolor(self):
        for colorJTOKEN in productjson['products']['details'][productID]['product']['colors']['options']:
            if str(colorJTOKEN['productId']) == str(productID):
                colorName = colorJTOKEN['name']
                return colorName

    def IgnoreProduct(self, response):
        productAvailability = response.xpath(
            "//link[@itemprop='availability']/@href").get()
        if not 'InStock' in productAvailability:
            return True
        else:
            return False

    def GetCategory(self, response):
        filterList = []
        if GetterSetter.ProductUrl in Spider_BaseClass.ProductUrlsAndCategory:
            categories = Spider_BaseClass.ProductUrlsAndCategory[GetterSetter.ProductUrl]
            for category in str(categories).split('$'):
                filterList.append(category)

        categoryTokens = productjson['products']['details'][productID]['product']['categories']
        for filterToken in categoryTokens:
            filterValue = filterToken["name"]
            filterList.append(filterValue)
        filters = '$'.join(set(filterList))
        return filters + 'Women'
