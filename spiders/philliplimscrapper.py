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


class PhillipLimScrapper(Spider_BaseClass):
    Spider_BaseClass.headersDict = {
        "Cookie": 'ctx=%7b%22u%22%3a5000013734912129%2c%22g%22%3a1%7d; ss=ezcfLu0eoEU0DDV4RvSIQlBviVBRUSfpscbV5zTqdnznwgz0YFAkB_BDPJz7hYw4EqGqk9mIAYE4n478HASn9sjylZNSLJSVFEmgItBRmbIooHmX9rq5CM4X_akQx4L9n_PZmEiG-ktwfHVltQJx427QiYQFMeSbqppg_DHjSRFaJCcYEWrcvjqzWL0NRN96ZGU-rIuRF3P3Rp6IT4iBrV6SP3y4FhdNaH6q5Nb2BbI; csi=b756cea0-1388-445d-bfbc-1393745fb061; dfUserSub=%2F; __cfruid=f44baf4646e3e2ef6ba635fa65a456eebd38213e-1651138248; __cf_bm=nofKtcONPVL43fk6OOhAJqxgXpXx3DjfuRE4QxW6P9o-1651138250-0-AQyM5r1WnlAy4vwbFygVCfCHFHe7XTVsycNJWCIa+P1/qx6CaJjn4mZnmBFXuOC/VkFHWa27iVQA5W9PPu1c8hta7tRFw4eBdWyT/nKK9OpYkoY2/jMCBu6zoF8+FvPAkQ==; _gcl_au=1.1.494695102.1651138253; forterToken=54d631c8bef84be78aa0d3c628c74ba8_1651138253165__UDF43_11ck; __cid=1dGVJLKqNrQemdBAoax7MRl-DPg1by-tGFlfsAhYdDVNW1Oyw3VLhR9mWfcHXByyZgeaF0xdISMZUAy8GmM3_lY3Kdl3NDKfLnZjkDMPOt5_NyTDOxYHkCpofYAgeATZdW5nizsgZYQgeCHGIWFqnitxc_d-OzjfNGpjgStoYoAqeBXZaT0132N3aok1aD-4eD1lgSxuYIZh01IkEz5n1SxpZYR_xG_xVR8f9TtwGt5vPT-cOxE9xH40e-IyeBv0Ox8h0WswOtNoeBfZaT0wxCgcYoE7LiDvLgdjkGsrDIVEaHoUDWlhnyhpfIEibmqcO2xpgCtiY4A7CB4fE1jmlaBYljpXk1FjG4X3sPxYuLHsbZjl1oassV-YUysbWFOwG1hTsBtYU7AbWFOwG1hTCXThPfAbGBOwG1hT8FsYE_Bb1lM-G8oqeNOakfkblsPQOVhTsBtYU7Ebpw; lastRskxRun=1651138255447; rskxRunCookie=0; rCookie=gcw26hg1gdhma7v0r8qt7dl2it33o9; _attn_=eyJ1Ijoie1wiY29cIjoxNjUxMTM4MjU1OTAxLFwidW9cIjoxNjUxMTM4MjU1OTAxLFwibWFcIjoyMTkwMCxcImluXCI6ZmFsc2UsXCJ2YWxcIjpcIjJhNWVlMWZmNmI3ZjQ4NjQ4MDRhZTg0NGZmZmQzOGZmXCJ9In0=; __attentive_id=2a5ee1ff6b7f4864804ae844fffd38ff; __attentive_cco=1651138255972; __attentive_pv=1; __attentive_ss_referrer="ORGANIC"; __attentive_dv=1; cto_bundle=tsd7JF9rJTJGUUczRGFSblVCY1EzQjM4eWpacnIzcyUyQllsYUZtS3RZcTJGJTJCbGhJNTFzSld1M2NkS3ozOHJTUHBlYWI1JTJGaG52Q3BqdlJUU28zUmNUc3BPSkpBdExrQ2h1dURsd2JCUkpscFQ5RW1NJTJGVm5NV0dqdjVycXFQN1glMkZMd1R3SE96UWtKdDhjblM5Zkp4cUtxVDB6Y1Vqb1ElM0QlM0Q; _ga=GA1.1.1002159748.1651138258; _gid=GA1.1.1127742511.1651138258; _gat_UA-29736466-1=1; _fbp=fb.1.1651138258817.1679011523; _hjSessionUser_2134850=eyJpZCI6IjQ3ZWJjOGUwLTcwZTItNTViZS1iYjMwLWY5ZGJlZmQ2MjUzOCIsImNyZWF0ZWQiOjE2NTExMzgyNjA1MjIsImV4aXN0aW5nIjpmYWxzZX0=; _hjFirstSeen=1; _hjIncludedInSessionSample=1; _hjSession_2134850=eyJpZCI6ImVkMWIzMmQ2LTI4ZGEtNGQ2ZC1iOWEwLTRkYTlkMWU2M2E5MyIsImNyZWF0ZWQiOjE2NTExMzgyNjA1MzAsImluU2FtcGxlIjp0cnVlfQ==; _hjAbsoluteSessionInProgress=0; __adroll_fpc=64ea1e19c8b40f961bed73cf260136a9-1651138260770; __ar_v4=%7CD3KNA6MYSVACDN7U7H6ZOU%3A20220428%3A1%7C5T5M4LOWTZCMNKOLYF253A%3A20220428%3A1%7CBGULKUNENBAC3HQUMZQIUF%3A20220428%3A1',
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:99.0) Gecko/20100101 Firefox/99.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5"
    }

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(PhillipLimScrapper, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        return spider

    # https://www.31philliplim.com/pk/commerce/changecountry?subf=%2F&returnUrl=/
    def GetProductUrls(self, homePageResponse):
        global homePageJson
        if re.search('window.__PRELOADED_STATE__ = ', homePageResponse.text):
            homePageJson = homePageResponse.text.split('window.__PRELOADED_STATE__ = ')[1].split('</script>')[
                0].strip()
        homePageJson = json.loads(homePageJson)
        # ============================== TOP CATEGORY =================================#
        for topNodes in homePageJson['navigation']['header']:
            if topNodes['title'] == 'Sale' or topNodes['title'] == 'Women':
                topcategoryTitle = topNodes['title']
                topcategoryLink = topNodes['link']
                if not topcategoryLink.startswith(store_url):
                    topcategoryLink = store_url.rstrip('/') + topcategoryLink
                # ============================== Category =================================#
                if topNodes['nodes'] and Enumerable(topNodes['nodes']).where(
                        lambda x: x['title'] == 'Sale' or x['title'] == 'Ready-to-Wear' or x[
                            'title'] == 'LIVE FREE').to_list():
                    categoryTokens = Enumerable(topNodes['nodes']).where(
                        lambda x: x['title'] == 'Sale' or x['title'] == 'Ready-to-Wear' or x[
                            'title'] == 'LIVE FREE').to_list()
                    for categoryNode in categoryTokens:
                        categoryNodeTitle = categoryNode['title']
                        categoryLink = categoryNode['link']
                        if not categoryLink.startswith(store_url):
                            categoryLink = store_url.rstrip('/') + categoryLink
                        # ============================== SUB Category =================================#
                        subCategoryTokens = Enumerable(categoryNode['nodes']).where(
                            lambda x: x['title'] == 'Dresses').to_list()
                        if subCategoryTokens:
                            for subCategoryNode in subCategoryTokens:
                                subCategoryNodeTitle = subCategoryNode['title']
                                subCategoryNodeLink = subCategoryNode['link']
                                if not subCategoryNodeLink.startswith(store_url):
                                    subCategoryNodeLink = store_url.rstrip('/') + subCategoryNodeLink
                                category = topcategoryTitle + " " + categoryNodeTitle + " " + subCategoryNodeTitle
                                # self.listing(subCategoryNodeLink, category)
                        else:
                            if categoryNode['link'] == None:
                                continue
                            else:
                                categoryNodeLink = categoryNode['link']
                                if not categoryNodeLink.startswith(store_url):
                                    categoryNodeLink = store_url.rstrip('/') + categoryNodeLink
                                category = topcategoryTitle + " " + categoryNodeTitle
                                # self.listing(categoryNodeLink, category)
                else:
                    if not str(topcategoryLink).startswith(store_url):
                        topcategoryLink = store_url.rstrip('/') + topcategoryLink
                    category = topcategoryTitle
                    # self.listing(topcategoryLink, category)
        return Spider_BaseClass.AllProductUrls

    def listing(self, categorylink, category):
        categoryJsonStr = ''
        CategoryLinkResponse = requests.get(categorylink)
        CategoryLinkResponse = HtmlResponse(url=categorylink, body=CategoryLinkResponse.text, encoding='utf-8')
        if re.search('window.__PRELOADED_STATE__ = ', CategoryLinkResponse.text):
            categoryJsonStr = CategoryLinkResponse.text.split('window.__PRELOADED_STATE__ = ')[1].split('</script>')[
                0].strip()
        CategoryPageJson = json.loads(categoryJsonStr)
        for productJTOKEN in CategoryPageJson['products']['listing']['entries']:
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
        productID = Enumerable(productjson['products']['details']['products']['result'].keys()).select(
            lambda x: x).first_or_default()
        color = self.getcolor()
        name = productjson['products']['details']['products']['result'][productID]['name']
        if not color == '' and not re.search(color, name):
            name = name + " - " + color
        return name

    def GetPrice(self, response):
        orignalPrice = productjson['products']['details']['products']['result'][productID]['price'][
            'includingTaxesWithoutDiscount']
        if orignalPrice != None:
            return float(str(orignalPrice).replace('$', '').replace(',', ''))
        else:
            regularPrice = productjson['products']['details']['products']['result'][productID]['price']['formatted'][
                'includingTaxesWithoutDiscount']
            return float(str(regularPrice).replace('$', '').replace(',', ''))

    def GetSalePrice(self, response):
        salePrice = productjson['products']['details']['products']['result'][productID]['price']['formatted'][
            'includingTaxes']
        if salePrice != None:
            return float(str(salePrice).replace("$", "").replace(',', ''))
        else:
            return 0

    def GetBrand(self, response):
        return productjson['products']['details']['products']['result'][productID]['brand']['name']

    def GetImageUrl(self, response):
        imageUrls = []
        for imageJTOKEN in productjson['products']['details']['products']['result'][productID]['resources']['details']:
            imageurl = imageJTOKEN['sources']['2048']
            imageUrls.append(imageurl)
        return imageUrls

    def GetDescription(self, response):
        description = ''
        descriptionJToken = productjson['products']['details']['products']['result'][productID]['information']
        if not descriptionJToken:
            description = productjson['products']['details']['products']['result'][productID]['description']['full']
        for descriptionTag in descriptionJToken:
            if descriptionTag['title'] == 'Description':
                description = descriptionTag['value']
        details = self.GetDetails(response)
        return description + " " + details

    def GetDetails(self, response):
        materialList = []
        careInstructionList = []
        compositionJTokens = productjson['products']['details']['products']['result'][productID]['composition']
        for compositionJToken in compositionJTokens:
            name = compositionJToken['material']
            value = compositionJToken['value']
            material = value + '% ' + name
            materialList.append(material)
        if materialList:
            materials = ' '.join(materialList)
        else:
            materials = ' '
        careInstructions = productjson['products']['details']['products']['result'][productID]['care']
        for careInstruction in careInstructions:
            value = careInstruction['value']
            careInstructionList.append(value)
        if careInstructionList:
            careInstructions = ' '.join(careInstructionList)
        else:
            careInstructions = ' '
        return materials + " " + careInstructions

    def GetSizes(self, response):
        productSizes = []
        merchantID = productjson['products']['details']['products']['result'][productID]['merchant']['id']
        gender = ProductFilters.objects.get(ProductUrl=GetterSetter.ProductUrl).ParentCategory.split(',')[0]
        for sizeJTOKEN in productjson['products']['details']['products']['result'][productID]['sizes']:
            sizeScale = sizeJTOKEN['scaleAbbreviation']
            for sizeQuantityToken in sizeJTOKEN['stock']:
                if sizeQuantityToken['merchantId'] == merchantID:
                    if sizeQuantityToken['quantity'] != 0:
                        sizeName = sizeJTOKEN['name']
                        fitType = GetFitType(gender, sizeName)
                        available = True
                        if sizeScale:
                            sizeName = sizeScale + " " + sizeName
                        colorName = self.getcolor()
                        sizelist = str(colorName), str(sizeName), available, str(fitType), 0.0, 0.0
                        productSizes.append(sizelist)
        return productSizes

    def getcolor(self):
        for colorJTOKEN in productjson['products']['details']['products']['result'][productID]['colors']['options']:
            if str(colorJTOKEN['productId']) == str(productID):
                colorName = colorJTOKEN['name']
                return colorName

    def IgnoreProduct(self, response):
        if re.search('"availability":', response.text):
            productAvailability = response.text.split('"availability":')[1].split(',')[0].strip()
            if not 'InStock' in productAvailability:
                return True
            else:
                return False

    def GetCategory(self, response):
        filterList = []
        siteMapCategory = str(Spider_BaseClass.ProductUrlsAndCategory[GetterSetter.ProductUrl]).replace('None', '')
        categoryTokens = productjson['products']['details']['products']['result'][productID]['categories']
        for filterToken in categoryTokens:
            filterValue = filterToken["name"]
            filterList.append(filterValue)
        breadCrumsJTokens = productjson['products']['details']['products']['result'][productID]['breadcrumbs']
        for breadCrumsJToken in breadCrumsJTokens:
            categoryName = breadCrumsJToken["name"]
            filterList.append(categoryName)
        filters = ' '.join(set(filterList))
        return siteMapCategory.strip() + " " + filters
