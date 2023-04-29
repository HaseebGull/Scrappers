import sys
from pathlib import Path

DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(DIR.parent.parent.parent.parent))
__package__ = DIR.name

import django

django.setup()
from Shopify import *
from BaseClass import Spider_BaseClass
from scrapy import signals

store_url = sys.argv[4]


class MatchesfashionScrapper(Spider_BaseClass):
    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(MatchesfashionScrapper, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        return spider

    def GetProductUrls(self, homePageResponse):
        genderList = ['women', 'men']
        # ========== Category And Subcategory ==========#
        topCategoryNodes = homePageResponse.xpath("//a[@class='menu__tab--womens']/@href")
        gender = Enumerable(genderList).where(lambda x: x in topCategoryNodes).first_or_default()
        for topCategoryNode in topCategoryNodes:
            topCategoryNodelink = topCategoryNode.xpath("./@href").get()
            if not topCategoryNodelink.startswith(store_url):
                topCategoryNodelink = store_url.rstrip('/') + topCategoryNodelink
            # print("TOP CATEGORY TITLE :", topCategoryNodeTitle)
            print("TOP CATEGORY LINK  :", topCategoryNodelink)
            categoryNodes = topCategoryNode.xpath(
                "./div/div/section/ul/li/a[contains(div/text(),'Dresses') or contains(div/text(),'Jumpsuits & Rompers')]")
            for categoryNode in categoryNodes:
                categoryNodeTitle = categoryNode.xpath("./div/text()").get().strip()
                categoryNodelink = categoryNode.xpath("./@href").get()
                if not categoryNodelink.startswith(store_url):
                    categoryNodelink = store_url.rstrip('/') + categoryNodelink
                print("CATEGORY TITLE :", categoryNodeTitle)
                print("CATEGORY LINK  :", categoryNodelink)
                categoryLinkResponse = requests.get(categoryNodelink)
                categoryLinkResponse = HtmlResponse(url=categoryNodelink, body=categoryLinkResponse.text,
                                                    encoding='utf-8')

                subCategoryNodes = categoryLinkResponse.xpath(
                    "//ul[contains(@class,'NavCategory')]/li[a[contains(@class,'selected')]]/ul/li/a")
                for subCategoryNode in subCategoryNodes:
                    subCategoryNodeTitle = subCategoryNode.xpath("./text()").get().strip()
                    subCategoryNodelink = subCategoryNode.xpath("./@href").get()
                    if not subCategoryNodelink.startswith(store_url):
                        subCategoryNodelink = store_url.rstrip('/') + subCategoryNodelink
                    print("SUB CATEGORY TITLE :", subCategoryNodeTitle)
                    print("SUB CATEGORY LINK  :", subCategoryNodelink)
                    category = categoryNodeTitle + " " + subCategoryNodeTitle
                    self.listing(subCategoryNodelink, category)
        return Spider_BaseClass.AllProductUrls

    def listing(self, subCategoryNodelink, category):
        subCategoryLinkResponse = requests.get(subCategoryNodelink)
        subCategoryLinkResponse = HtmlResponse(url=subCategoryNodelink, body=subCategoryLinkResponse.text,
                                               encoding='utf-8', )
        product_list = subCategoryLinkResponse.xpath("//a[@class='url']/@href").extract()
        for productUrl in product_list:
            if not productUrl.startswith(store_url):
                productUrl = store_url.rstrip('/') + productUrl
            if re.search('https://', productUrl) and re.search('.htm', productUrl):
                productUrl = 'https://' + productUrl.split('https://')[1].split('.htm')[0].strip() + '.htm'
            print("Product URL  :", productUrl)
            Spider_BaseClass.AllProductUrls.append(productUrl)
            siteMapCategory = str(Spider_BaseClass.ProductUrlsAndCategory.get(productUrl)).replace('None', '')
            if siteMapCategory:
                Spider_BaseClass.ProductUrlsAndCategory[productUrl] = siteMapCategory + " " + category
            else:
                Spider_BaseClass.ProductUrlsAndCategory[productUrl] = category
        try:
            nextPageUrl = subCategoryLinkResponse.xpath(
                "(//a[contains(@class,'next') and not(contains(@class,'disabled'))]/@data-next-link)[1]").extract()[0]
            if not nextPageUrl.startswith(store_url):
                nextPageUrl = store_url.rstrip('/') + nextPageUrl
            print('nextPageUrl:', nextPageUrl)
            self.listing(nextPageUrl, category)
        except:
            pass

    def GetName(self, response):
        global productJsonStr
        if re.search('data-key="pdp.state">', response.text):
            productJsonStr = response.text.split('data-key="pdp.state">')[1].split('</script>')[0].strip()
            productJsonStr = json.loads(productJsonStr)

        colorName = productJsonStr['product']['defaultStyleColor']['color']['label']
        name = productJsonStr['product']['shortDescription']
        if not colorName == '' and not re.search(colorName, name):
            name = name + ' - ' + colorName
        return name

    def GetPrice(self, response):
        originalPrice = productJsonStr['product']["defaultStyleColor"]['prices'][0]['retailAmount']
        return originalPrice

    def GetSalePrice(self, response):
        price = productJsonStr['product']["defaultStyleColor"]['prices'][0]['saleAmount']
        return price

    def GetBrand(self, response):
        brand = productJsonStr["product"]["brandLabel"]
        return brand

    def GetImageUrl(self, response):
        imageUrls = []
        imageTokens = productJsonStr['product']["defaultStyleColor"]['images']
        for imageToken in imageTokens:
            imageUrl = imageToken["url"]
            imageUrls.append(imageUrl)
        return imageUrls

    def GetDescription(self, response):
        description = productJsonStr["product"]["longDescription"]
        return description

    def GetSizes(self, response):
        productSizes = []
        colorName = productJsonStr['product']['defaultStyleColor']['color']['label']
        sizeTokens = productJsonStr['product']['styleColors']
        for sizetoken in sizeTokens:
            for size in sizetoken['styleColorSizes']:
                if size['inStock'] == True:
                    sizename = size['size']['label']
                    # sizeName = fitType + "$" + sizeName
                    available = True
                    sizeList = str(colorName), str(sizename), available, 0.0, 0.0
                    productSizes.append(sizeList)
        return productSizes

    def GetCategory(self, response):
        filterList = []
        if GetterSetter.ProductUrl in Spider_BaseClass.ProductUrlsAndCategory:
            categories = Spider_BaseClass.ProductUrlsAndCategory[GetterSetter.ProductUrl]
            for category in str(categories).split('$'):
                filterList.append(category)

        filter = str(productJsonStr['product']['classification']).split('/')
        filterList.append(filter)
        filters = '$'.join(map(str, filterList)) + '$'
        return filters
