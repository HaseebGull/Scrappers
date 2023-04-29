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


class ProenzaSchoulerScrapper(Spider_BaseClass):
    Spider_BaseClass.cookiesDict = {
        "Cookie": "dfUserSub=%2Fpk; ctx=%7b%22u%22%3a5000011595252650%2c%22g%22%3a1%7d; ss=aWErI549mT1Jt_rLGg_wplkhU3btFVCJ_K6shoTrTdHcfN5EjSSKMtrj1OfW5kOROL-eV-bb1CVQpDXNLlPxCRNvMM8MX4uqFP8NkYmzUR8AuQiiUSHnrX3Pv8OLHhsSRoPDj0SXSFSnM-QoxoZ8bjSLtQ-Td_XF4ZrFFiUccUyR4HhbK6H_psUXPg_rTenfrOKViMaInEVnZOSJ-goILcn3cyR0CeKiDKRIfGNxpR4; csi=f399c596-d4a3-41b7-8611-98876ce18ffb; __cf_bm=d2Bm6lDHF1O5iJbCucbJj8_2Dx8mkzXk_Nx5jinrN5g-1643774132-0-AVLq+MJoZyGU/P/3LLbFUPqP22SVUuPdB6TqLhMn6cm9AVKCXMvgm/R3kHT+EH2GTSkJT1yxZfbv8LeFHbFEqX/yPZcX3jpgx3mAtyawa74lGj+iQAw1jfbMoP0pC5W23g==; agreedToCookiePolicy=true; ku1-sid=PpqDiYoS5erG369QwLDiu; ku1-vid=480b4916-fc6b-cd1f-6e73-9835dd7333f1; _gcl_au=1.1.1502339130.1643774133; forterToken=bd1e4450e5be4d2cb0f7ce59b1215892_1643774133626__UDF43_11ck; __cid=_Pi8sofqm62fvQ59cEn_q_mNnAuG3D-xQiqIqlIroy8XKISomQacn0UVju2tK9umQBDg5AxE_sMtR-WFdAW0iml87cQlRPPZYWXQinAbqpp6C9PDLx2wkWFTsp56C_bcexKyhHECpO0kSO_Fbhm0m3EbtZpwC8LDM07ixTkEvZxvG-iiIk6ym3Ydt5w7oIU-SU2wz3Yasp4lt87rD2zI72EDzcQ1TuiCEwKk4gULw9ggW-zDIlik7ihZ4ck1GMCbcAvy2R4e25phW_f1dHS0hmFvt-5wGqmYcQW1k28asYR0GracaI-Qm24aq5t4HLSGYR6-mnERtJphaskFSSsxj_orQS5K4IZ5QfYgqqYrb6u2HYAupXl7qwXjhDlBK4QTQf2EEvErhKpBK4SqQSuEECCR5QvgazqqQSuE6gFrxOoBuOM-JlfxaYKVOuQIwgjy1SuGqkErhLhA1A; _uetsid=f8cb14d083db11ecb0bdb98a36ca1c4e; _uetvid=f8cb175083db11ec8304d709d2673b34; stc114744=tsa:1643774133762.1622123271.1486046.8480004638517414.:20220202042533|env:1%7C20220305035533%7C20220202042533%7C1%7C1042363:20230202035533|uid:1643774133761.784309894.145468.114744.1603521960.1:20230202035533|srchist:1042363%3A1%3A20220305035533:20230202035533; _pin_unauth=dWlkPU5HTTFZV0ZoT1RRdFl6azFNaTAwTmpKaExXSTRORFF0TVRaaE9XSXpZVGcwTmprNA; lastRskxRun=1643774134875; rskxRunCookie=0; rCookie=impicmz9q7oqgriaert8vkz50ofvh; _ga=GA1.2.1442784236.1643774136; _gid=GA1.2.1028464223.1643774136; _clck=eltvqt|1|eyn|0; _clsk=q1p8zy|1643774137863|1|1|b.clarity.ms/collect; _gat_UA-11844021-1=1; _hjSessionUser_1549962=eyJpZCI6IjU5OTU1NTk5LTUwZjQtNTRiMC1iMmIzLWJiYmE2NDMzNDI1NiIsImNyZWF0ZWQiOjE2NDM3NzQxMzgzNjcsImV4aXN0aW5nIjpmYWxzZX0=; _hjFirstSeen=1; _hjSession_1549962=eyJpZCI6ImM5YTI5MjQ5LTVkNTctNDFlZi04YjFmLTE0MmFmYjBiMDJiNCIsImNyZWF0ZWQiOjE2NDM3NzQxMzgzOTksImluU2FtcGxlIjpmYWxzZX0=; _hjAbsoluteSessionInProgress=0; cto_bundle=kpYNcV9hYXNWcm14RzFRek0lMkZITXNWTFl3eXJCdkFrSGJIcUxaZENuN3o5aFQ3Q0hTZWROTVA5cUpRRFU5cEdwRSUyRnBVb3M5ekFhenV4YUt4c2g0Q2UlMkJCZ3FrYVhqdEV0Vm5IbDlRVlkxRG44Nlg3U0x2dGclMkZBVkR2WWklMkZjRyUyQlF0dzl4cFY4U24lMkJWVzkyWUxOMW1QOWlOZyUyRiUyRnclM0QlM0Q"}

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(ProenzaSchoulerScrapper, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        return spider

    def GetProductUrls(self, homePageResponse):
        global homePageJson
        if re.search('window.__PRELOADED_STATE__ = ', homePageResponse.text):
            homePageJson = homePageResponse.text.split('window.__PRELOADED_STATE__ = ')[1].split('</script>')[
                0].strip()
        homePageJson = json.loads(homePageJson)
        # ============================== TOP CATEGORY =================================#
        for topNodes in homePageJson['navigation']['scopes']['main']:
            if 'Proenza Schouler' in topNodes['title'] or topNodes['title'] == 'Sale':
                topcategoryTitle = topNodes['title']
                topcategoryLink = topNodes['link']['url']
                if not topcategoryLink.startswith(store_url):
                    topcategoryLink = store_url.rstrip('/') + topcategoryLink
                # ============================== Category =================================#
                if topNodes['children'] and Enumerable(topNodes['children']).where(
                        lambda x: x['title'] == 'Clothing' or x['title'] == ' New Arrivals' or x[
                            'title'] == 'Proenza Schouler Sale' or x['title'] == 'White Label Sale').to_list():
                    categoryTokens = Enumerable(topNodes['children']).where(
                        lambda x: x['title'] == 'Clothing' or x['title'] == ' New Arrivals'
                                  or x['title'] == 'Proenza Schouler Sale'
                                  or x['title'] == 'White Label Sale').to_list()
                    for categoryNode in categoryTokens:
                        categoryNodeTitle = categoryNode['title']
                        # ============================== SUB Category =================================#
                        subCategoryTokens = Enumerable(categoryNode['children']).where(
                            lambda x: x['title'] == 'Dresses').to_list()
                        if subCategoryTokens:
                            for subCategoryNode in subCategoryTokens:
                                subCategoryNodeTitle = subCategoryNode['title']
                                subCategoryNodeLink = subCategoryNode['link']['url']
                                if not subCategoryNodeLink.startswith(store_url):
                                    subCategoryNodeLink = store_url.rstrip('/') + subCategoryNodeLink
                                category = 'Women ' + topcategoryTitle + " " + categoryNodeTitle + " " + subCategoryNodeTitle
                                print(category)
                                # self.listing(subCategoryNodeLink, category)
                        else:
                            if categoryNode['link']['url'] == None:
                                continue
                            else:
                                categoryNodeLink = categoryNode['link']['url']
                                if not categoryNodeLink.startswith(store_url):
                                    categoryNodeLink = store_url.rstrip('/') + categoryNodeLink
                                category = 'Women ' + topcategoryTitle + " " + categoryNodeTitle
                                print(category)
                                # self.listing(categoryNodeLink, category)
                    else:
                        if not str(topcategoryLink).startswith(store_url):
                            topcategoryLink = store_url.rstrip('/') + topcategoryLink
                        category = 'Women ' + topcategoryTitle
                        print(category)
                        # self.listing(topcategoryLink, category)
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
            Spider_BaseClass.AllProductUrls.append(productUrl)
            siteMapCategory = str(Spider_BaseClass.ProductUrlsAndCategory.get(productUrl)).replace('None', '')
            if siteMapCategory:
                Spider_BaseClass.ProductUrlsAndCategory[productUrl] = siteMapCategory + " " + category
            else:
                Spider_BaseClass.ProductUrlsAndCategory[productUrl] = category
        try:
            nextPageUrl = CategoryLinkResponse.xpath("//link[@rel='next']/@href").extract()[0]
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
            global productjson
            if re.search('window.__PRELOADED_STATE__ = ', response.text):
                productjson = response.text.split('window.__PRELOADED_STATE__ = ')[1].split('</script>')[
                    0].strip()
            productjson = json.loads(productjson)
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
        gender = ProductFilters.objects.get(ProductUrl=GetterSetter.ProductUrl).ParentCategory.split(',')[0]
        colorName = self.getcolor()
        for sizeJTOKEN in productjson['products']['details'][productID]['product']['sizes']:
            sizeName = sizeJTOKEN['name']
            fitType = GetFitType(gender, str(sizeName).strip())
            available = True
            sizelist = str(colorName), str(sizeName), str(available), str(fitType), 0.0, 0.0
            productSizes.append(sizelist)
        return productSizes

    def getcolor(self):
        for colorJTOKEN in productjson['products']['details'][productID]['product']['colors']['options']:
            if str(colorJTOKEN['productId']) == str(productID):
                colorName = colorJTOKEN['name']
                return colorName

    def IgnoreProduct(self, response):
        preOrderNode = response.xpath(
            "//button[contains(@data-test,'product-button') and contains(text(),'Pre-Order')]").get()
        if preOrderNode:
            return True
        productAvailability = response.xpath("//link[@itemprop='availability']/@href").get()
        if not 'InStock' in productAvailability:
            return True

        return False

    def GetCategory(self, response):
        filterList = []
        siteMapCategory = str(Spider_BaseClass.ProductUrlsAndCategory.get(GetterSetter.ProductUrl)).replace('None', '')
        categoryTokens = productjson['products']['details'][productID]['product']['categories']
        for filterToken in categoryTokens:
            filterValue = filterToken["name"]
            filterList.append(filterValue)
        filters = '$'.join(set(filterList))
        return siteMapCategory + " " + filters
