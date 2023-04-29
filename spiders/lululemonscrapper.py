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


class LululemonScrapper(Spider_BaseClass):
    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(LululemonScrapper, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        return spider

    def GetProductUrls(self, homePageResponse):
        # ========== Category And Subcategory ==========#
        gender_nodes = homePageResponse.xpath(
            "//ul[contains(@class,'links_categoryNavItems')]/li/a[contains(text(),'All Women')]")
        for category_node in gender_nodes:
            category_title = category_node.xpath('./text()').get().strip()
            print("Category: ", category_title)

            category_link = category_node.xpath('./@href').get()
            if not category_link.startswith(store_url):
                category_link = store_url + category_link
            category_link = category_link.split('/_')[0]
            print(category_title, " :", category_link)
            category_link_response = requests.get(category_link, stream=True)
            category_link_response = HtmlResponse(url=category_link, body=category_link_response.text, encoding='utf-8')
            sub_category_nodes = category_link_response.xpath(
                "//ul[@class='swiper-wrapper']/li/a[contains(text(),'Dresses')]")
            for sub_category_node in sub_category_nodes:
                sub_category_title = str(sub_category_node.xpath('./text()').get()).strip()
                sub_category_link = sub_category_node.xpath('./@href').get()
                if not sub_category_link.startswith(store_url):
                    sub_category_link = store_url + sub_category_link
                sub_category_link = sub_category_link.split('/_')[0]
                category = category_title + " " + sub_category_title
                self.listing(sub_category_link, category)
                print(sub_category_title, ":", sub_category_link)
        return Spider_BaseClass.AllProductUrls

    def listing(self, sub_category_link, category):
        CategoryLinkResponse = requests.get(sub_category_link)
        categoryPageResponse = HtmlResponse(url=sub_category_link, body=CategoryLinkResponse.text, encoding='utf-8')
        collection_name = '"' + categoryPageResponse.url.split('/')[-1] + '"'
        print(collection_name)
        api_url = "https://shop.lululemon.com/snb/graphql"
        query = {
            "query": "query getCategoryDetails($category: String!, $cid: String, $forceMemberCheck: Boolean, $nValue: String!, $sl: String!, $locale: String!, $Ns: String, $storeId: String, $pageSize: Int, $page: Int, $onlyStore: Boolean) {\n  categoryDetails(\n    category: $category\n    nValue: $nValue\n    locale: $locale\n    sl: $sl\n    Ns: $Ns\n    page: $page\n    pageSize: $pageSize\n    storeId: $storeId\n    onlyStore: $onlyStore\n    forceMemberCheck: $forceMemberCheck\n    cid: $cid\n  ) {\n    activeCategory\n    categoryLabel\n    fusionExperimentId\n    fusionExperimentVariant\n    fusionQueryId\n    h1Title\n    isBopisEnabled\n    isFusionQuery\n    isWMTM\n    name\n    results: totalProducts\n    totalProductPages\n    currentPage\n    type\n    bopisProducts {\n      allAvailableSizes\n      currencyCode\n      defaultSku\n      displayName\n      listPrice\n      parentCategoryUnifiedId\n      productOnSale: onSale\n      productSalePrice: salePrice\n      pdpUrl\n      productCoverage\n      repositoryId: productId\n      productId\n      inStore\n      unifiedId\n      skuStyleOrder {\n        colorGroup\n        colorId\n        colorName\n        inStore\n        size\n        sku\n        skuStyleOrderId\n        styleId01\n        styleId02\n        styleId\n        __typename\n      }\n      swatches {\n        primaryImage\n        hoverImage\n        url\n        colorId\n        inStore\n        __typename\n      }\n      __typename\n    }\n    storeInfo {\n      totalInStoreProducts\n      totalInStoreProductPages\n      storeId\n      __typename\n    }\n    products {\n      allAvailableSizes\n      currencyCode\n      defaultSku\n      displayName\n      listPrice\n      parentCategoryUnifiedId\n      productOnSale: onSale\n      productSalePrice: salePrice\n      pdpUrl\n      productCoverage\n      repositoryId: productId\n      productId\n      inStore\n      unifiedId\n      skuStyleOrder {\n        colorGroup\n        colorId\n        colorName\n        inStore\n        size\n        sku\n        skuStyleOrderId\n        styleId01\n        styleId02\n        styleId\n        __typename\n      }\n      swatches {\n        primaryImage\n        hoverImage\n        url\n        colorId\n        inStore\n        __typename\n      }\n      __typename\n    }\n    seoLinks {\n      next\n      prev\n      self\n      __typename\n    }\n    __typename\n  }\n}\n",
            "operationName": "getCategoryDetails",
            "variables": {"nValue": "N-8s3",
                          "category": collection_name, "locale": "en_US", "sl": "US", "page": 1, "pageSize": 9,
                          "forceMemberCheck": False}}
        self.get_product_url(query, category)
        api_response = requests.post(api_url, json=query)
        api_response = json.loads(api_response.content.decode('utf-8'))
        page_no = 2
        total_pages = api_response['data']['categoryDetails']['totalProductPages']
        print(total_pages)
        while page_no <= total_pages:
            query = {
                "query": "query getCategoryDetails($category: String!, $cid: String, $forceMemberCheck: Boolean, $nValue: String!, $sl: String!, $locale: String!, $Ns: String, $storeId: String, $pageSize: Int, $page: Int, $onlyStore: Boolean) {\n  categoryDetails(\n    category: $category\n    nValue: $nValue\n    locale: $locale\n    sl: $sl\n    Ns: $Ns\n    page: $page\n    pageSize: $pageSize\n    storeId: $storeId\n    onlyStore: $onlyStore\n    forceMemberCheck: $forceMemberCheck\n    cid: $cid\n  ) {\n    activeCategory\n    categoryLabel\n    fusionExperimentId\n    fusionExperimentVariant\n    fusionQueryId\n    h1Title\n    isBopisEnabled\n    isFusionQuery\n    isWMTM\n    name\n    results: totalProducts\n    totalProductPages\n    currentPage\n    type\n    bopisProducts {\n      allAvailableSizes\n      currencyCode\n      defaultSku\n      displayName\n      listPrice\n      parentCategoryUnifiedId\n      productOnSale: onSale\n      productSalePrice: salePrice\n      pdpUrl\n      productCoverage\n      repositoryId: productId\n      productId\n      inStore\n      unifiedId\n      skuStyleOrder {\n        colorGroup\n        colorId\n        colorName\n        inStore\n        size\n        sku\n        skuStyleOrderId\n        styleId01\n        styleId02\n        styleId\n        __typename\n      }\n      swatches {\n        primaryImage\n        hoverImage\n        url\n        colorId\n        inStore\n        __typename\n      }\n      __typename\n    }\n    storeInfo {\n      totalInStoreProducts\n      totalInStoreProductPages\n      storeId\n      __typename\n    }\n    products {\n      allAvailableSizes\n      currencyCode\n      defaultSku\n      displayName\n      listPrice\n      parentCategoryUnifiedId\n      productOnSale: onSale\n      productSalePrice: salePrice\n      pdpUrl\n      productCoverage\n      repositoryId: productId\n      productId\n      inStore\n      unifiedId\n      skuStyleOrder {\n        colorGroup\n        colorId\n        colorName\n        inStore\n        size\n        sku\n        skuStyleOrderId\n        styleId01\n        styleId02\n        styleId\n        __typename\n      }\n      swatches {\n        primaryImage\n        hoverImage\n        url\n        colorId\n        inStore\n        __typename\n      }\n      __typename\n    }\n    seoLinks {\n      next\n      prev\n      self\n      __typename\n    }\n    __typename\n  }\n}\n",
                "operationName": "getCategoryDetails",
                "variables": {"nValue": "N-8s3",
                              "category": collection_name, "locale": "en_US", "sl": "US", "page": page_no,
                              "pageSize": 9, "forceMemberCheck": False}}
            self.get_product_url(query, category)
            page_no += 1

    def get_product_url(self, query, category):
        global product_url
        api_url = "https://shop.lululemon.com/snb/graphql"
        api_response = requests.post(api_url, json=query)
        api_response = json.loads(api_response.content.decode('utf-8'))
        for proToken in api_response['data']['categoryDetails']['products']:
            product_url = (store_url + proToken['pdpUrl'])
            product_url = product_url.split('/_')[0]
            print("URLS = ", product_url)
            Spider_BaseClass.AllProductUrls.append(product_url)
            siteMapCategory = str(Spider_BaseClass.ProductUrlsAndCategory.get(product_url)).replace('None', '')
            if siteMapCategory:
                Spider_BaseClass.ProductUrlsAndCategory[product_url] = siteMapCategory + " " + category
            else:
                Spider_BaseClass.ProductUrlsAndCategory[product_url] = category

    def GetProducts(self, response):
        ignorProduct = self.IgnoreProduct(response)
        if ignorProduct == True:
            self.ProductIsOutofStock(GetterSetter.ProductUrl)
        categoryAndName = self.GetCategory(response) + " " + self.GetName(response)
        if (re.search('Sale', categoryAndName, re.IGNORECASE) or
            re.search('New', categoryAndName, re.IGNORECASE)) and not \
                re.search(r'\b((shirt(dress?)|jump(suit?)|dress|set|gown|suit|caftan)(s|es)?)\b', categoryAndName,
                          re.IGNORECASE):
            print('Skipping Non Dress Product')
            self.ProductIsOutofStock(GetterSetter.ProductUrl)
        else:
            self.GetProductInfo(response)

    def GetName(self, response):
        color = self.GetSelectedColor(response)
        name = str(response.xpath("//div[@itemprop='name']/text()").get()).strip()
        if not color == '' and not re.search(color, name, re.I):
            name = name + " - " + color
        print("name =", name)
        return name

    def GetSelectedColor(self, response):
        color = str(response.xpath("//span[contains(@class,'selection_colorName')]/text()").get()).strip()
        return color

    def GetPrice(self, response):
        orignalPrice = response.xpath(
            "//div[contains(@class,'priceWrapper')]//span[contains(@class,'price')]//text()").get()
        if orignalPrice != None:
            return float(str(orignalPrice).strip().replace('$', '').replace(',', ''))
        else:
            regularPrice = response.xpath(
                "//div[contains(@class,'priceWrapper')]//span[contains(text(),'Sale Price')]/following-sibling::span[1]/text()").get()
            return float(str(regularPrice).strip().replace('$', '').replace(',', ''))

    def GetSalePrice(self, response):
        salePrice = response.xpath(
            "//div[contains(@class,'priceWrapper')]//span[contains(text(),'Sale Price')]/following-sibling::span[1]/text()").get()
        if salePrice != None:
            return float(str(salePrice).strip().replace('$', '').replace(',', ''))
        else:
            return 0

    def GetBrand(self, response):
        return str("lululemon")

    def GetImageUrl(self, response):
        imageUrls = []
        image_nodes = response.xpath(
            "//img[contains(@class,'productImages')]")
        for image in image_nodes:
            umage_url = image.xpath("./@srcset").get().split("320w,\n")[1].split('?')[0]
            imageUrls.append(umage_url)
        return imageUrls

    def GetDescription(self, response):
        return ' '.join(response.xpath("//div[contains(@class,'accordionItemPanel-ULkCp')]//text()").extract()).strip()

    def GetSizes(self, response):
        sizes = []
        sizeList = response.xpath(
            "//div[contains(@class,'TileGroupWrapper')]/div/span[not(contains(@class,'sizeTileDisabled'))]")
        gender = ProductFilters.objects.get(ProductUrl=GetterSetter.ProductUrl).ParentCategory.split(',')[0]
        color = self.GetSelectedColor(response)
        for size in sizeList:
            sizename = size.xpath("./text()").get().strip()
            available = True
            fitType = GetFitType(gender, sizename)
            sizes.append((color, sizename, available, fitType, 0.0, 0.0))
        return sizes

    def GetCategory(self, response):
        siteMapCategory = str(Spider_BaseClass.ProductUrlsAndCategory.get(GetterSetter.ProductUrl)).replace('None', '')
        return "Women " + siteMapCategory

