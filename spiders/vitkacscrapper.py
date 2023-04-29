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


class VitkacScrapper(Spider_BaseClass):
    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(VitkacScrapper, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        return spider

    def GetProductUrls(self, homePageResponse):
        # ========== Category And Subcategory ==========#
        topCategoryNodes = homePageResponse.xpath(
            "//ul[@class='menu-main']/li/a[contains(text(),'Women') or contains(text(),'Men') or contains(text(),'Kids')]")
        for topCategoryNode in topCategoryNodes:
            topCategoryTitle = topCategoryNode.xpath("./text()").get().strip()
            topCategoryLink = topCategoryNode.xpath("./@href").get()
            subNavId = topCategoryNode.xpath("./@data-target").get().strip()

            categoryNodes = topCategoryNode.xpath(
                "//ul[contains(@id,'" + subNavId + "')]/li/a[contains(text(),'CLOTHING') or contains(text(),'New') or contains(text(),'Sale') or contains(text(),'BABY') or contains(text(),'GIRLS') or contains(text(),'BOY')]")
            for categoryNode in categoryNodes:
                categoryTitle = categoryNode.xpath("./text()").get().strip()
                categorylink = categoryNode.xpath("./@href").get()
                subcatId = categoryNode.xpath("./@data-target").get()
                if not categorylink.startswith(store_url):
                    categorylink = store_url.rstrip('/') + categorylink

                subCategoryNodes = categoryNode.xpath("//section[contains(@class,'submenu-main-box')]/div[@id='" + str(
                    subcatId) + "']/div/div/a[contains(text(),'Dresses') or contains(text(),'Jumpsuits') or contains("
                                "text(),'Suits') or contains(text(),'Baby clothes') or contains(text(),'sets') or "
                                "contains(text(),'Clothing') or contains(text(),'Baby (0-36 months)') or contains("
                                "text(),'Boys clothes (4-14 years)') or contains(text(),'Girls clothes (4-14 "
                                "years)')]")
                for subCategoryNode in subCategoryNodes:
                    subCategoryTitle = subCategoryNode.xpath("./text()").get().strip()
                    subCategorylink = subCategoryNode.xpath("./@href").get()
                    if not subCategorylink.startswith(store_url):
                        subCategorylink = store_url.rstrip('/') + subCategorylink
                    if topCategoryTitle == 'Men' and (
                            categoryTitle == 'New' or categoryTitle == 'Sale') and subCategoryTitle == 'Clothing':
                        continue

                    category = topCategoryTitle + " " + categoryTitle + " " + subCategoryTitle
                    self.listing(subCategorylink, category)
        return Spider_BaseClass.AllProductUrls

    def listing(self, categorylink, category):
        CategoryLinkResponse = requests.get(categorylink)
        CategoryLinkResponse = HtmlResponse(url=categorylink, body=CategoryLinkResponse.text,
                                            encoding='utf-8')
        self.GetUrls(CategoryLinkResponse, category)
        pageCount = 2
        maxPage = CategoryLinkResponse.xpath("//p[@class='max']/span/text()")
        while maxPage and int(maxPage.get().strip()) >= pageCount:
            try:
                nextpageUrl = CategoryLinkResponse.xpath("(//a[contains(@class,'pager-next')]/@href)[1]").get()
                if not nextpageUrl.startswith(store_url):
                    nextpageUrl = store_url.rstrip('/') + nextpageUrl
                CategoryLinkResponse = requests.get(nextpageUrl)
                CategoryLinkResponse = HtmlResponse(url=nextpageUrl, body=CategoryLinkResponse.text,
                                                    encoding='utf-8')
                self.GetUrls(CategoryLinkResponse, category)
                pageCount += 1
            except:
                pass

    def GetUrls(self, CategoryLinkResponse, category):
        product_list = CategoryLinkResponse.xpath("//a[@class='box-click']/@href").extract()
        for productUrl in product_list:
            if not productUrl.startswith(store_url):
                productUrl = store_url.rstrip('/') + productUrl
            Spider_BaseClass.AllProductUrls.append(productUrl)
            siteMapCategory = str(Spider_BaseClass.ProductUrlsAndCategory.get(productUrl)).replace('None', '')
            if siteMapCategory:
                Spider_BaseClass.ProductUrlsAndCategory[productUrl] = siteMapCategory + " " + category
            else:
                Spider_BaseClass.ProductUrlsAndCategory[productUrl] = category

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
        name = str(response.xpath("//div[contains(@class,'prod-header-module')]/h1/span/text()").get().strip()).replace(
            '’', '').replace('‘', '')
        if not color == '' and not re.search(color, name):
            name = name + ' - ' + color
        return name

    def GetSelectedColor(self, response):
        try:
            if response.xpath("//small[contains(text(),'colour:') or contains(text(),'Colour:')]/text()").get():
                color = response.xpath("//small[contains(text(),'colour:')]/text()").get().replace('colour: ', '')
            else:
                color = str(response.xpath("//div[@id='productAvailability']/div/p/span/text()").get().strip()).split(
                    '-')
                if len(color) >= 2:
                    color = str(
                        response.xpath("//div[@id='productAvailability']/div/p/span/text()").get().strip()).split('-')[
                        -1]
                    if color.isalnum():
                        color = ''
        except Exception as e:
            color = ''
        return color

    def GetPrice(self, response):
        orignalPrice = response.xpath("//p[@id='salePrice']/text()")
        if orignalPrice:
            return float(str(orignalPrice.get().strip()).replace('$', '').replace(',', ''))
        else:
            regularPrice = response.xpath(
                "//span[@id='regularPrice']/text()").get().strip()
            return float(str(regularPrice).replace('$', '').replace(',', ''))

    def GetSalePrice(self, response):
        salePrice = response.xpath(
            "//span[@id='regularPrice']/text()")
        if salePrice:
            return float(str(salePrice.get().strip()).replace('$', '').replace(',', ''))
        else:
            return 0

    def GetDescription(self, response):
        try:
            descriptionList = response.xpath(
                "//div[@id='panel1' or @id='panel2']/p[@class='productDescription']/text()").extract()
            description = ' '.join(descriptionList)
        except:
            description = ''

        return description

    def GetBrand(self, response):
        return response.xpath("//div[contains(@class,'prod-header-module')]/h1/a/text()").get().strip()

    def GetImageUrl(self, response):
        imageUrls = []
        images = response.xpath("//div[@class='slide']/p/a/@href").extract()
        for image in images:
            imageUrls.append(image)
        return imageUrls

    def GetSizes(self, response):
        sizes = []
        sizeList = response.xpath(
            "//div[@id='product_sizes']/ul/li/a[not(contains(@class,'empty'))]/text()[1]").extract()
        gender = ProductFilters.objects.get(ProductUrl=GetterSetter.ProductUrl).ParentCategory.split(',')[0]
        color = self.GetSelectedColor(response)
        for size in sizeList:
            available = True
            fitType = GetFitType(gender, str(size).strip())
            sizes.append([color, str(size).strip(), available, fitType, 0.0, 0.0])
        return sizes

    # def IgnoreProduct(self, response):
    #     if re.search('"availability":', response.text):
    #         productAvailability = response.text.split('"availability":')[1].split(',')[0].strip()
    #         if not 'InStock' in productAvailability:
    #             return True
    #         else:
    #             return False

    def GetCategory(self, response):
        siteMapCategory = str(Spider_BaseClass.ProductUrlsAndCategory.get(GetterSetter.ProductUrl)).replace('None', '')
        return siteMapCategory.strip()
