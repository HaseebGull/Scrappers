from BaseClass import *


class OptionsProperty():
    def __init__(self):
        self._sizeOptionNames = ['size', 'sizing', 'title']
        self._colorOptionNames = ['color', 'colour', 'style']
        self._ignoreOptionNames = []

    @property
    def sizeOptionNames(self):
        return self._sizeOptionNames

    @sizeOptionNames.setter
    def sizeOptionNames(self, value):
        self._sizeOptionNames = value

    @property
    def colorOptionNames(self):
        return self._colorOptionNames

    @colorOptionNames.setter
    def colorOptionNames(self, value):
        self._colorOptionNames = value

    @property
    def ignoreOptionNames(self):
        return self._ignoreOptionNames

    @ignoreOptionNames.setter
    def ignoreOptionNames(self, value):
        self._ignoreOptionNames = value


class shopify(Spider_BaseClass):
    global productJson
    optPropObj = OptionsProperty()
    Spider_BaseClass.cookiesDict = {"cart_currency": "USD"}

    def GetProducts(self, response):
        ignorProduct = self.IgnoreProduct(response)
        if ignorProduct:
            self.ProductIsOutofStock(GetterSetter.ProductUrl)
        else:
            shopify.productJson = json.loads(self.SetProductJson(response))
            self.GetProductInfo(response)

    def SetProductJson(self, response):
        if re.search('products.push\({', response.text):
            productJsonStr = '{' + response.text.split('Afterpay.products.push({')[1].split('"content"')[
                0].strip().rstrip(
                ',') + '}'
        elif re.search('products.push = {', response.text):
            productJsonStr = '{' + response.text.split('var product = {')[1].split('"content"')[0].strip().rstrip(
                ',') + '}'
        elif re.search('_BISConfig.product = {', response.text):
            productJsonStr = '{' + response.text.split('_BISConfig.product = {')[1].split('"content"')[
                0].strip().rstrip(
                ',') + '}'
        elif re.search('"product": {', response.text):
            productJsonStr = '{' + response.text.split('"product": {')[1].split('"content"')[0].strip().rstrip(
                ',') + '}'
        elif re.search('SwymProductInfo.product = {', response.text):
            productJsonStr = '{' + response.text.split('SwymProductInfo.product = {')[1].split('"content"')[
                0].strip().rstrip(',') + '}'
        else:
            print("Invoke product json api for: ", GetterSetter.ProductUrl)
            productJsonStr = requests.get(GetterSetter.ProductUrl + '.js',
                                          cookies=Spider_BaseClass.cookiesDict).content

        return productJsonStr

    def GetName(self, response):
        return shopify.productJson["title"]

    def GetPrice(self, response):
        compareAtPrice = shopify.productJson['compare_at_price']
        if compareAtPrice and compareAtPrice != 0:
            if shopify.productJson["compare_at_price_min"] == shopify.productJson["compare_at_price_max"]:
                return float(compareAtPrice / 100)

            availableVariants = Enumerable(shopify.productJson['variants']).where(
                lambda x: x["available"] == True and x["compare_at_price"] != None)
            if availableVariants:
                return float(availableVariants[0]["compare_at_price"] / 100)

            return float(compareAtPrice / 100)
        else:
            if shopify.productJson["price_min"] == shopify.productJson["price_max"]:
                return float(shopify.productJson["price"] / 100)

            availableVariants = Enumerable(shopify.productJson['variants']).where(lambda x: x["available"] == True)
            if availableVariants:
                return float(availableVariants[0]["price"] / 100)

            return float(shopify.productJson["price"] / 100)

    def GetSalePrice(self, response):
        compareAtPrice = shopify.productJson['compare_at_price']
        if compareAtPrice:
            if shopify.productJson["price_min"] == shopify.productJson["price_max"]:
                return float(shopify.productJson["price"] / 100)

            availableVariants = Enumerable(shopify.productJson['variants']).where(lambda x: x["available"] == True)
            if availableVariants:
                return float(availableVariants[0]["price"] / 100)

            return float(shopify.productJson["price"] / 100)
        else:
            return 0.0

    def GetCategory(self, response):
        filterList = []
        for filter in shopify.productJson['tags']:
            filterList.append(filter)
        filters = ' '.join(map(str, filterList))

        siteMapCategory = str(Spider_BaseClass.ProductUrlsAndCategory.get(GetterSetter.ProductUrl)).replace('None', '')
        return (Spider_BaseClass.testingGender + " " + siteMapCategory + " " + filters).strip()

    def GetBrand(self, response):
        return shopify.productJson['vendor']

    def GetDescription(self, response):
        return shopify.productJson['description']

    def GetImageUrl(self, response):
        imageUrls = []
        for src in shopify.productJson['images']:
            imageUrls.append(src)
        return imageUrls

    def GetSizes(self, response):
        position = -1
        colourName = ''
        productSizes = []
        sizePositions = []
        colorPositions = []
        ignorePositions = []

        for option in shopify.productJson['options']:
            try:
                if option['name']:
                    sizeMatch = list(
                        filter(lambda x: x.lower() in str(option['name']).lower(), shopify.optPropObj.sizeOptionNames))
                    colorMatch = list(
                        filter(lambda x: x.lower() in str(option['name']).lower(), shopify.optPropObj.colorOptionNames))
                    ignoreMatch = list(
                        filter(lambda x: x.lower() in str(option['name']).lower(),
                               shopify.optPropObj.ignoreOptionNames))

                    if ignoreMatch:
                        if position < 0:
                            position = option['position'] + position
                            ignorePositions.append(position)
                        else:
                            position = option['position']
                            ignorePositions.append(position)
                    elif sizeMatch:
                        if position < 0:
                            position = option['position'] + position
                            sizePositions.append(position)
                        else:
                            position = option['position']
                            sizePositions.append(position)
                    elif colorMatch:
                        if position < 0:
                            position = option['position'] + position
                            colorPositions.append(position)
                        else:
                            position = option['position'] + position
                            colorPositions.append(position)
                    else:
                        raise Exception("Unknown Position: ", option['name'])
                    position = -1
            except:
                sizeMatch = list(filter(lambda x: x.lower() in str(option).lower(), shopify.optPropObj.sizeOptionNames))
                colorMatch = list(
                    filter(lambda x: x.lower() in str(option).lower(), shopify.optPropObj.colorOptionNames))
                ignoreMatch = list(
                    filter(lambda x: x.lower() in str(option).lower(), shopify.optPropObj.ignoreOptionNames))
                if ignoreMatch:
                    position = position + 1
                    ignorePositions.append(position)
                elif sizeMatch:
                    position = position + 1
                    sizePositions.append(position)
                elif colorMatch:
                    position = position + 1
                    colorPositions.append(position)
                else:
                    raise Exception("Unknown Position: ", option['name'])

        gender = ProductFilters.objects.get(ProductUrl=GetterSetter.ProductUrl).ParentCategory.split(',')[0]

        for variant in shopify.productJson['variants']:
            if colorPositions:
                if len(colorPositions) == 1:
                    colourName = variant['options'][colorPositions[0]]
                else:
                    colourName = variant['options'][colorPositions[0]] + "/" + variant['options'][colorPositions[1]]

            if sizePositions:
                if len(sizePositions) == 1:
                    sizeName = variant['options'][sizePositions[0]]
                else:
                    sizeName = variant['options'][sizePositions[0]] + "/" + variant['options'][sizePositions[1]]
            else:
                sizeName = "One Size"

            compareAtPrice = variant['compare_at_price']
            if compareAtPrice and compareAtPrice != 0:
                sizePrice = compareAtPrice / 100
                sizeSalePrice = variant['price'] / 100
            else:
                sizeSalePrice = 0.0
                sizePrice = variant['price'] / 100

            fitType = GetFitType(gender, sizeName)

            available = bool(variant["available"])

            sizeList = str(colourName).title(), str(sizeName), available, str(
                fitType), float(sizePrice), float(sizeSalePrice)
            productSizes.append(sizeList)

        return productSizes

    # NonCanonical Url: https://www.culturekings.com.au/collections/mens-tops-muscle-tees/products/carre-carre-blinds-capone-muscle-tee-black
    # Canonical url: https://www.culturekings.com.au/products/carre-carre-blinds-capone-muscle-tee-black
    def GetCanonicalUrl(self, product_link):
        if re.search("/collections/", product_link) and re.search("/products/", product_link):
            product_link = product_link.split('/collections/')[0] + '/products/' + product_link.split('/products/')[1]
        return product_link
