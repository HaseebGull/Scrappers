from BaseClass import *


class OptionsProperty():
    def __init__(self):
        self._sizeOptionNames = ['size', 'sizing', 'title', 'ca_misura']
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


class magento(Spider_BaseClass):
    global productJson
    global productID
    optPropObj = OptionsProperty()

    def GetProducts(self, response):
        ignorProduct = self.IgnoreProduct(response)
        if ignorProduct == True:
            self.ProductIsOutofStock(GetterSetter.ProductUrl)
        else:
            jsonStr = self.SetProductJson(response.text)
            if jsonStr != '':
                magento.productJson = json.loads(jsonStr)

            productID = response.xpath("//input[@name='product']/@value").get()
            self.GetProductInfo(response)

    def SetProductJson(self, response):
        if re.search("new Product.Config\(", response):
            return response.split("new Product.Config(")[1].split(");")[0]
        return ''

    def GetName(self, response):
        return response.xpath("//span[@itemprop='name']/text()").get()

    def GetPrice(self, response):
        orignalPrice = response.xpath(
            "//div[@class='pdp__info' or @class='product-info-price']//div[@data-product-id='" + productID + "']/span/span[contains(@data-price-type,'finalPrice')]/span/text()").get()
        if orignalPrice != None:
            return float(str(orignalPrice).replace('$', '').replace(',', ''))
        else:
            regularPrice = response.xpath(
                "//div[@class='pdp__info' or @class='product-info-price']//div[@data-product-id='" + productID + "']//span[@data-price-type='oldPrice']/span/text()").get()
            return float(str(regularPrice).replace('$', '').replace(',', ''))

    def GetSalePrice(self, response):
        salePrice = response.xpath(
            "//div[@class='pdp__info' or @class='product-info-price']//div[@data-product-id='" + productID + "']//span[@data-price-type='finalPrice']/span/text()").get()
        if salePrice:
            return float(str(salePrice).replace('$', '').replace(',', ''))
        else:
            return 0

    def GetImageUrl(self, response):
        imageUrl = []
        data = response.xpath(
            "//script[@type='text/x-magento-init' and contains(text(),'gallery/gallery')]").get()
        if data:
            imageJsonStr = '{"data":' + data.split('data":')[1].split('}],')[0].strip().rstrip(',') + '}]}'
            imageJson = json.loads(imageJsonStr)
            for imageToken in imageJson['data']:
                imageUrl.append(imageToken['img'])
        return imageUrl

    def GetCategory(self, response):
        siteMapCategory = str(Spider_BaseClass.ProductUrlsAndCategory.get(GetterSetter.ProductUrl)).replace('None', '')
        return (Spider_BaseClass.testingGender + " " + siteMapCategory).strip()

    def GetDescription(self, response):
        return ','.join(response.xpath("//div[@itemprop='description']/text()").extract())

    def GetBrand(self, response):
        return response.xpath("//a[contains(@class,'brand-name')]/text()").get()

    def GetSizes(self, response):
        sizes = ''
        sizeOptions = []
        colorOptions = []
        ignoreOptions = []
        productSizes = []

        attributeKeys = magento.productJson['attributes'].keys()
        for attributeKey in attributeKeys:
            for ignoreOptionName in magento.optPropObj.ignoreOptionNames:
                if re.search(ignoreOptionName, magento.productJson['attributes'][attributeKey]['code'],
                             re.IGNORECASE):
                    ignoreOptions.append(magento.productJson['attributes'][attributeKey]['id'])

            for colorOptionName in magento.optPropObj.colorOptionNames:
                if re.search(colorOptionName, magento.productJson['attributes'][attributeKey]['code'],
                             re.IGNORECASE) and not Enumerable(ignoreOptions).where(
                    lambda x: x == magento.productJson['attributes'][attributeKey]['id']).first_or_default():
                    colorOptions.append(magento.productJson['attributes'][attributeKey]['id'])

            for sizeOptionName in magento.optPropObj.sizeOptionNames:
                if re.search(sizeOptionName, magento.productJson['attributes'][attributeKey]['code'],
                             re.IGNORECASE) and not Enumerable(ignoreOptions).where(
                    lambda x: x == magento.productJson['attributes'][attributeKey]['id']).first_or_default():
                    sizeOptions.append(magento.productJson['attributes'][attributeKey]['id'])

        if not colorOptions and not ignoreOptions and not sizeOptions:
            raise Exception(
                "Unknown Attribute Code: " + magento.productJson['attributes'][list(attributeKeys)[0]]['code'])

        gender = ProductFilters.objects.get(ProductUrl=GetterSetter.ProductUrl).ParentCategory.split(',')[0]

        if colorOptions:
            for colourOption in magento.productJson['attributes'][colorOptions[0]]['options']:
                if colourOption['products'] is None:
                    continue
                else:
                    colorName = colourOption['label']
                    colorProducts = colourOption['products']
                    sizes = self.GetSizesOptions(magento.productJson, colorName, colorProducts, sizeOptions,
                                                 productSizes, gender)

        else:
            sizes = self.GetSizesOptions(magento.productJson, '', '', sizeOptions, productSizes, gender)
        return sizes

    def GetSizesOptions(self, dataJson, colorName, colorProducts, sizeOptions, productSizes, gender):
        if len(sizeOptions) == 2:
            for firstSizeOption in dataJson['attributes'][sizeOptions[0]]['options']:
                for secondSizeOption in dataJson['attributes'][sizeOptions[1]]['options']:
                    sizeName = firstSizeOption['label'] + "/" + secondSizeOption['label']

                    fitType = GetFitType(gender, sizeName)

                    firstSizeProducts = firstSizeOption['products']
                    secondSizeProducts = secondSizeOption['products']
                    if not firstSizeProducts:
                        available = False
                    else:
                        try:
                            if int(firstSizeOption[0]['stock_status']) == 0:
                                available = False
                            elif int(firstSizeOption[0]['qty']) == 0:
                                available = False
                            else:
                                available = True
                        except:
                            available = bool(set.intersection(set(firstSizeProducts), set(secondSizeProducts)))

                    if set(firstSizeProducts) != set(secondSizeProducts):
                        raise Exception(
                            "First Products: ", firstSizeProducts + " Second Products: ",
                                                secondSizeProducts + " are Different")

                    sizePrice, sizeSalePrice = self.GetSizePrice(firstSizeProducts)
                    sizeList = str(colorName).title(), str(sizeName), available, str(fitType), float(
                        sizePrice), float(sizeSalePrice)
                    productSizes.append(sizeList)
        else:
            for firstSizeOption in dataJson['attributes'][sizeOptions[0]]['options']:
                sizeName = firstSizeOption['label']

                fitType = GetFitType(gender, sizeName)

                firstSizeProducts = firstSizeOption['products']
                try:
                    if int(firstSizeOption[0]['stock_status']) == 0:
                        available = False
                    elif int(firstSizeOption[0]['qty']) == 0:
                        available = False
                    else:
                        available = True
                except:
                    if colorProducts:
                        available = bool(set.intersection(set(colorProducts), set(firstSizeProducts)))
                    else:
                        if firstSizeProducts:
                            available = True
                        else:
                            available = False

                sizePrice, sizeSalePrice = self.GetSizePrice(firstSizeProducts)
                sizeList = str(colorName).title(), str(sizeName), available, str(fitType), float(sizePrice), float(
                    sizeSalePrice)
                productSizes.append(sizeList)

        return productSizes

    def GetSizePrice(self, firstSizeProducts):
        if firstSizeProducts and magento.productJson["optionPrices"]:
            sizePrice = magento.productJson["optionPrices"][firstSizeProducts[0]]["oldPrice"]["amount"]
            if sizePrice:
                sizeSalePrice = magento.productJson["optionPrices"][firstSizeProducts[0]]["finalPrice"][
                    "amount"]
            else:
                sizeSalePrice = sizePrice
        elif magento.productJson["prices"]:
            sizePrice = magento.productJson["prices"]["oldPrice"]["amount"]
            if sizePrice:
                sizeSalePrice = magento.productJson["prices"]["finalPrice"]["amount"]
            else:
                sizeSalePrice = sizePrice
        elif magento.productJson["oldPrice"]:
            sizePrice = magento.productJson["oldPrice"]
            if sizePrice:
                sizeSalePrice = magento.productJson["finalPrice"]
                if not sizeSalePrice:
                    sizeSalePrice = magento.productJson["basePrice"]
            else:
                sizeSalePrice = sizePrice
        else:
            sizePrice = 0.0
            sizeSalePrice = 0.0
        return sizePrice, sizeSalePrice
