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


class SheinScrapper(Spider_BaseClass):
    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(SheinScrapper, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        return spider

    def GetProductUrls(self, homePageResponse):
        # ========== Category And Subcategory ==========#
        url = 'https://us.shein.com/get_categories?_lang=en&_ver=1.1.8'
        headers = {"Accept": "/", "X-Requested-With": "XMLHttpRequest"}
        homePageResponse = requests.get(url=url, headers=headers)
        homePageJson = json.loads(homePageResponse.text)
        topCategoryNodes = Enumerable(homePageJson).where(
            lambda x: x['name'] == 'WOMEN' or x['name'] == 'CURVE + PLUS' or x['name'] == 'KIDS').to_list()
        for topCategoryNode in topCategoryNodes:
            topCategorytitle = topCategoryNode['name']
            if topCategorytitle == 'CURVE + PLUS':
                topCategorytitle = 'Women ' + topCategorytitle
            categoryNodes = Enumerable(topCategoryNode['child']).where(
                lambda x: x['name'] == 'NEW IN' or
                          x['name'] == 'SALE' or
                          x['name'] == 'CLOTHING' or
                          x['name'] == 'ACTIVEWEAR' or
                          x['name'] == 'BABY' or
                          x['name'] == 'TODDLER GIRLS' or
                          x['name'] == 'TODDLER BOYS' or
                          x['name'] == 'BOYS' or
                          x['name'] == 'GIRLS'
            ).to_list()
            for categoryNode in categoryNodes:
                categoryTitle = categoryNode['name']
                subCategoryNodesJToken = Enumerable(categoryNode['child']).where(
                    lambda x: x['type'] != "6" and x['type'] != "16").to_list()
                subCategoryNodes = Enumerable(subCategoryNodesJToken).where(
                    lambda x: x['name'] == "NEW IN WOMEN'S CLOTHING" or
                              x['name'] == 'SHOP BY CATEGORY' or
                              x['name'] == 'DRESSES' or
                              x['name'] == 'JUMPSUITS & BODYSUITS' or
                              x['name'] == 'ACTIVEWEAR' or
                              x['name'] == 'NEW IN CURVE + PLUS' or
                              x['name'] == 'JUMPSUITS' or
                              x['name'] == 'ROMPERS' or
                              x['name'] == 'BODYSUITS' or
                              x['name'] == 'SUITS' or
                              x['name'] == 'WEDDING' or
                              x['name'] == 'NEW IN GIRLS' or
                              x['name'] == 'NEW IN TODDLER GIRLS' or
                              x['name'] == 'NEW IN BABY' or
                              x['name'] == 'NEW IN MATERNITY' or
                              x['name'] == 'BABY COTHING' or
                              x['name'] == 'NEW BORN (0-6MOS)' or
                              x['name'] == 'TWO PIECES SETS' or
                              x['name'] == 'TODDLER GIRLS' or
                              x['name'] == 'TODDLER BOYS' or
                              x['name'] == 'BOYS' or
                              x['name'] == 'GIRLS'

                ).to_list()
                for subCategoryNode in subCategoryNodes:
                    subSategoryTitle = subCategoryNode['name']
                    subSategoryLink = subCategoryNode['relativeUrl']
                    if not subSategoryLink.startswith(store_url):
                        subSategoryLink = store_url.rstrip('/') + subSategoryLink
                    try:
                        subSubCategoryNodes = Enumerable(subCategoryNode['child']).where(
                            lambda x: x['name'] == 'New In Dresses' or
                                      x['name'] == 'New In Jumpsuits & Bodysuits' or
                                      x['name'] == 'Dresses' or
                                      x['name'] == 'Blazer & Suits' or
                                      x['name'] == 'Jumpsuits' or
                                      x['name'] == 'Bodysuits' or
                                      x['name'] == 'Skirt Sets' or
                                      x['name'] == 'Shorts Sets' or
                                      x['name'] == 'Pants Sets' or
                                      x['name'] == 'Jumpsuits' or
                                      x['name'] == 'Bodysuits' or
                                      x['name'] == 'Sports Sets' or
                                      x['name'] == 'Active Dresses' or
                                      x['name'] == 'New In Jumpsuits & Matching Sets' or
                                      x['name'] == 'Jumpsuits & Co-ords' or
                                      x['name'] == 'Jumpsuits' or
                                      x['name'] == 'Sets' or
                                      x['name'] == 'Onesies' or
                                      x['name'] == 'Photography Sets' or
                                      x['name'] == 'Tee Sets' or
                                      x['name'] == 'Cami Sets' or
                                      x['name'] == 'Track Short Sets' or
                                      x['name'] == 'Sweatpants Sets' or
                                      x['name'] == 'Skirt Sets' or
                                      x['name'] == 'Short Sets' or
                                      x['name'] == 'Pant Sets' or
                                      x['name'] == 'Cami Dresses' or
                                      x['name'] == 'A Line Dresses' or
                                      x['name'] == 'Floral Dresses' or
                                      x['name'] == 'Partywear' or
                                      x['name'] == 'Bodycon Dresses' or
                                      x['name'] == 'Flower Girl Dresses'

                        ).to_list()
                        for subSubCategoryNode in subSubCategoryNodes:
                            subSubSategoryTitle = subSubCategoryNode['name']
                            subSubSategoryLink = subSubCategoryNode['relativeUrl']
                            if not subSubSategoryLink.startswith(store_url):
                                subSubSategoryLink = store_url.rstrip('/') + subSubSategoryLink
                            category = topCategorytitle + " - " + categoryTitle + " - " + subSategoryTitle + " - " + subSubSategoryTitle
                            self.listing(subSubSategoryLink, category)
                    except:
                        category = topCategorytitle + " - " + categoryTitle + " - " + subSategoryTitle
                        self.listing(subSategoryLink, category)
        return Spider_BaseClass.AllProductUrls

    def listing(self, categorylink, category):
        CategoryLinkResponse = requests.get(categorylink)
        CategoryLinkResponse = HtmlResponse(url=categorylink, body=CategoryLinkResponse.text, encoding='utf-8')
        jsonStr = CategoryLinkResponse.text.split('var gbProductListSsrData = ')[1].split('</script>')[0].strip()
        listingJson = json.loads(jsonStr)
        totalProducts = listingJson['results']['sum']
        pageNo = 2
        totalPages = 0
        if totalProducts % 120 == 0:
            totalPages = totalProducts / 120
        else:
            totalPages = totalProducts / 120 + 1

        if totalPages > 40:
            totalPages = 40
        self.GetUrls(listingJson, category)
        while totalPages >= pageNo:
            if re.search('\?page=', categorylink):
                categorylink = categorylink.split('page')[0].rstrip('? | &')

            if re.search('\?', categorylink):
                nextPageUrl = categorylink + '&page=' + str(pageNo) + ''
            else:
                nextPageUrl = categorylink + '?page=' + str(pageNo) + ''
            CategoryLinkResponse = requests.get(nextPageUrl)
            CategoryLinkResponse = HtmlResponse(url=nextPageUrl, body=CategoryLinkResponse.text, encoding='utf-8')
            jsonStr = CategoryLinkResponse.text.split('var gbProductListSsrData = ')[1].split('</script>')[
                0].strip()
            listingJson = json.loads(jsonStr)
            self.GetUrls(listingJson, category)
            pageNo += 1

    def GetUrls(self, listingJson, category):
        for productJToken in listingJson['results']['goods']:
            productUrl = ''
            if not productJToken['relatedColor']:
                productUrl = store_url + str(productJToken['goods_url_name']).replace(' ', '-') + '-p-' + str(
                    productJToken['goods_id']) + '-cat-' + str(productJToken['cat_id']) + '.html'
                Spider_BaseClass.AllProductUrls.append(productUrl)
            else:
                productJTokens = productJToken['relatedColor']
                for productJToken in productJTokens:
                    productUrl = store_url + str(productJToken['goods_url_name']).replace(' ', '-') + '-p-' + str(
                        productJToken['goods_id']) + '-cat-' + str(productJToken['cat_id']) + '.html'
                    Spider_BaseClass.AllProductUrls.append(productUrl)

            siteMapCategory = str(Spider_BaseClass.ProductUrlsAndCategory.get(productUrl)).replace('None', '')
            if siteMapCategory:
                Spider_BaseClass.ProductUrlsAndCategory[productUrl] = siteMapCategory + " " + category
            else:
                Spider_BaseClass.ProductUrlsAndCategory[productUrl] = category

    def GetProducts(self, response):
        global productJson
        ignorProduct = self.IgnoreProduct(response)
        if ignorProduct == True:
            self.ProductIsOutofStock(GetterSetter.ProductUrl)
        else:
            jsonStr = response.text.split('productIntroData: ')[1].split('abt: ')[0].strip().rstrip(',')
            productJson = json.loads(jsonStr)
            categoryAndName = self.GetCategory(response) + " " + self.GetName(response)
            if (re.search('Sale', categoryAndName, re.IGNORECASE) or
                re.search(r'\b' + 'NEW IN MATERNITY' + r'\b', categoryAndName, re.IGNORECASE) or
                re.search(r'\b' + 'Blazer & Suits' + r'\b', categoryAndName, re.IGNORECASE) or
                re.search(r'\b' + 'ACTIVEWEAR' + r'\b', categoryAndName, re.IGNORECASE) or
                re.search(r'\b' + 'NEW IN GIRLS' + r'\b', categoryAndName, re.IGNORECASE) or
                re.search(r'\b' + 'NEW IN TODDLER GIRLS' + r'\b', categoryAndName, re.IGNORECASE) or
                re.search(r'\b' + 'NEW IN BABY' + r'\b', categoryAndName, re.IGNORECASE)

            ) and not \
                    re.search(
                        r'\b((shirt(dress?)|jump(suit?)|dress|gown|romper|sleep((wear?)|(suit?))|suit|bodysuit|caftan)(s|es)?)\b',
                        categoryAndName,
                        re.IGNORECASE):
                print('Skipping Non Dress Product')
                self.ProductIsOutofStock(GetterSetter.ProductUrl)
            else:
                self.GetProductInfo(response)

    def IgnoreProduct(self, response):
        if re.search('"availability":"', response.text) and not re.search('InStock',
                                                                          response.text.split('"availability":"')
                                                                          [1].split('"}}')[0].strip()):
            return True

        if response.xpath("//button[@type='button' and contains(text(),'This product is no longer available.')]"):
            return True

        return False

    def GetName(self, response):
        color = self.GetSelectedColor(response)
        name = productJson['detail']['goods_name']
        if not color == '' and not re.search(color, name, re.I):
            name = name + " - " + color
        return name

    def GetSelectedColor(self, response):
        selectdColorJTokens = productJson['detail']['productDetails']
        for selectdColorJToken in selectdColorJTokens:
            if selectdColorJToken['attr_name'] == 'Color':
                selectdColor = selectdColorJToken['attr_value']
                return selectdColor

    def GetPrice(self, response):
        orignalPrice = productJson['detail']['retailPrice']['usdAmount']
        if orignalPrice != None:
            return orignalPrice  # float(orignalPrice / 100)
        else:
            return 0

    def GetSalePrice(self, response):

        salePrice = productJson['detail']['salePrice']['usdAmount']
        if salePrice != None:
            return salePrice  # float(salePrice / 100)
        else:
            return 0.0

    def GetBrand(self, response):
        if productJson['detail']['brand']:
            return productJson['detail']['brand']
        else:
            return 'Shein'

    def GetImageUrl(self, response):
        imageUrls = []
        mainImage = productJson['goods_imgs']['main_image']['origin_image']
        imageUrls.append(mainImage)
        images = productJson['goods_imgs']['detail_image']
        for image in images:
            imageUrls.append(image['origin_image'])
        return imageUrls

    def GetDescription(self, response):
        description = []
        descriptionJTokens = productJson['detail']['productDetails']
        for descriptionJToken in descriptionJTokens:
            jsonDescription = descriptionJToken['attr_name'] + ' : ' + descriptionJToken['attr_value']
            description.append(jsonDescription)
        description = ' '.join(description)
        return description

    def GetSizes(self, response):
        productSizes = []
        productID = productJson['detail']['goods_id']
        colorName = self.GetSelectedColor(response)
        sizeJToken = productJson['attrSizeList']['sale_attr_list'][str(productID)]['sku_list']
        gender = ProductFilters.objects.get(ProductUrl=GetterSetter.ProductUrl).ParentCategory.split(',')[0]
        for size in sizeJToken:
            sizeName, orignalPrice, salePrice = '', '', ''
            sizeTokens = size['sku_sale_attr']
            for sizeToken in sizeTokens:
                if sizeToken['attr_name'] == 'Size':
                    sizeName = sizeToken['attr_value_name']

            orignalPrice = size['price']['retailPrice']['usdAmount']
            salePrice = size['price']['salePrice']['usdAmount']

            stock = size['stock']
            if stock > 0:
                available = True
            else:
                available = False

            sizeNameWithUsSizes = productJson['localSizeList']['size_rule_list']
            for sizeNameWithUsSize in sizeNameWithUsSizes:
                if sizeNameWithUsSize['name'] == sizeName:
                    sizeName = sizeNameWithUsSize['name'] + '(' + sizeNameWithUsSize['correspond'] + ')'
                else:
                    continue

            fitType = GetFitType(gender, sizeName)
            sizelist = str(colorName), str(sizeName), available, str(fitType), orignalPrice, salePrice
            productSizes.append(sizelist)
        return productSizes

    def GetCategory(self, response):
        filterList = []
        siteMapCategory = str(Spider_BaseClass.ProductUrlsAndCategory.get(GetterSetter.ProductUrl)).replace('None', '')
        # categoryJToken = productjson['props']['initialState']['entities']['product'][sku]['hierarchicalCategories']
        # for category in categoryJToken:
        #     filterList.append(category['label'])
        # filters = '$'.join(map(str, filterList))
        return 'Women ' + siteMapCategory
