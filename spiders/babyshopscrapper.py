import sys
from pathlib import Path

DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(DIR.parent.parent.parent.parent))
__package__ = DIR.name

import django

django.setup()
from scrapy import signals
from BaseClass import *

store_url = sys.argv[4]


class BabyshopScrapper(Spider_BaseClass):
    Spider_BaseClass.cookiesDict = {
        "Cookie": "png.state=AprlkP8606fgujZ1NKOyufO4sBtqlZ1zdhIHVd+Y5zwCElkqQKh2pQKXGjnOazvpSX/WMW/LifsNytUd4zo6Ol7LA6KYFIrxzRiVlAeCXBRbSvD4bURXzNJeAeu8cksM5Tn0aw==; bsg-ab-test-recNLJTBNCTyDpIeL=%7B%22userId%22%3A60%2C%22name%22%3A%22Babyshop%20product%20listings%22%2C%22group%22%3A%22GroupB%22%2C%22shareInBGroup%22%3A100%7D; UseExternalProductListing=true; bsg-search-state=%7B%22enable_image_reranks%22%3Afalse%2C%22ranking_model_version%22%3A%22b%22%7D; bsg-ab-test-subgroup-recxX2A7uGNH9iNwj=%7B%22mainGroupUserId%22%3A60%2C%22subgroupUserId%22%3A81%2C%22name%22%3A%22Babyshop%20Picture%20with%20Face%22%2C%22subgroup%22%3A%22Babyshop_PictureWithFace_False%22%2C%22mainGroup%22%3A%22Babyshop%20product%20listings%22%2C%22mainGroupAB%22%3A%22GroupB%22%7D; cf-trust-score=77; cf-bot=false; __cf_bm=pN.GhMUQ7OyMPn6UrkLaqWtmD5DTpm_EFjkw_f.NA4A-1652411748-0-AchIur7gJu8KSaSru/f5CG9KAun4k05jcc0lcALAExS+SKHYHhN/e1V8SVNEIShHek6f96wkDWJGycKUIz+Nuz0=; consensus-popup-pageviews-counter=1; regional-popup-pageviews-counter=1; newsletter-popup-pageviews-counter=1; sizeguide-popup-pageviews-counter=1; sg_cookies={%225618601%22:{%22vid%22:%22b7d8f6be-a47b-49c2-9ad9-e6db263fec44%22%2C%22lw%22:%225-12-20-15%22%2C%22rf%22:%22%22%2C%22pw%22:1%2C%22tc%22:5%2C%22tv%22:1%2C%22192515657_ch%22:%22-1%22%2C%22192516960_ch%22:%22-1%22%2C%22192517364_ch%22:%22-1%22%2C%22192517877_ch%22:%22-1%22%2C%22fp%22:1754637438}}; _gcl_au=1.1.2099647404.1652411753; _ga_L8DRBV98YP=GS1.1.1652411753.1.0.1652411773.0; _ga=GA1.1.2108471819.1652411754; BSGCS=ok; _uetsid=00a58d20d26b11ec93c0e313e3b6cfa7; _uetvid=00a58820d26b11ecbe2f57b50a70ad4f; scarab.visitor=%225998C86A7F9C6376%22; _pin_unauth=dWlkPVlXVTBNVFl4TlRZdFkyUmtZaTAwTnpjMExUZzBOall0TW1Wa1l6aGhNekJtTmpJMA; cebs=1; _ce.s=v~34c3dfbc4533bb109a8c0378dbd46b1e238c9c48~vpv~0; _hjSessionUser_1678138=eyJpZCI6IjQyMTcyMGIwLTg1MDgtNTQ5NS04YjE3LTA3YmZjZjg0Zjc0OSIsImNyZWF0ZWQiOjE2NTI0MTE3NTcyODYsImV4aXN0aW5nIjpmYWxzZX0=; _hjFirstSeen=1; _hjIncludedInSessionSample=0; _hjSession_1678138=eyJpZCI6IjU5NjJlMTQzLWFiYTMtNGRjZi04YmJiLTAxNDk1ZTYyNTE5NSIsImNyZWF0ZWQiOjE2NTI0MTE3NTc1NTYsImluU2FtcGxlIjpmYWxzZX0=; _hjAbsoluteSessionInProgress=0; _clck=qtihg5|1|f1f|0; _ym_uid=1652411760706949351; _ym_d=1652411760; _clsk=jk3dji|1652411759873|1|1|l.clarity.ms/collect; _fbp=fb.1.1652411760006.1610320243; _ym_visorc=w; _ym_isad=2; _gid=GA1.2.2074327213.1652411765; bsga-storage=%7B%22cookieId%22%3A%2218a170c9-1e54-492e-b9e8-6688a72b8a76%22%2C%22tracker%22%3A%22babyshop%22%2C%22version%22%3A2%7D; _gat_UA-2368336-1=1; bsga-session=%7B%22sessionId%22%3A%22a2ae8a1b-5b40-4b5c-9564-b6d01929b496%22%2C%22ip%22%3A%22182.188.94.124%22%7D; bsg-ab-test-subgroup-recJ6XFdzVVe7bqw1=%7B%22mainGroupUserId%22%3A60%2C%22subgroupUserId%22%3A25%2C%22name%22%3A%22Babyshop%20listings%20custom%20ranking%22%2C%22subgroup%22%3A%22Babyshop_RerankModel_B%22%2C%22mainGroup%22%3A%22Babyshop%20product%20listings%22%2C%22mainGroupAB%22%3A%22GroupB%22%7D"}
    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(BabyshopScrapper, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        return spider

    def GetProductUrls(self, homePageResponse):
        # ========== Category And Subcategory ==========#
        topCategoryNodes = homePageResponse.xpath(
            "//nav[@class='navigation']/div/a[contains(text(),'New In')]")
        for topCategoryNode in topCategoryNodes:
            topCategoryTitle = topCategoryNode.xpath("./text()").get().strip()
            topCategorylink = topCategoryNode.xpath("./@href").get()
            if not topCategorylink.startswith(store_url):
                topCategorylink = store_url.rstrip('/') + topCategorylink
            topCategoryJsonStr = topCategoryNode.xpath("./@data-json").get()
            HomePageJson = json.loads(topCategoryJsonStr)
            containList = ["New Arrivals - Children's Clothes", "Baby Clothes", "Dresses",
                           "Suits", "Clothing Sets", "Rainwear", "Sleepwear", "UV-Clothing & Swimwear"]
            for key, value in HomePageJson.items():
                if value['name'] in containList:
                    categoryTitle = value['name']
                    categoryLink = value['url']
                    if not categoryLink.startswith(store_url):
                        categoryLink = store_url.rstrip('/') + categoryLink
                    if categoryTitle == 'Dresses':
                        category = "Baby Girl " + topCategoryTitle + " " + categoryTitle
                    elif categoryTitle == 'Suits':
                        category = "Boy " + topCategoryTitle + " " + categoryTitle
                    elif categoryTitle == 'Clothing Sets' or categoryTitle == 'Rainwear' or \
                            categoryTitle == 'Sleepwear' or categoryTitle == 'UV-Clothing & Swimwear':
                        category = 'Baby ' + topCategoryTitle + " " + categoryTitle
                    elif "Children's" in categoryTitle:
                        category = 'Baby ' + topCategoryTitle + " " + categoryTitle
                    else:
                        category = topCategoryTitle + " " + categoryTitle
                    self.listing(categoryLink, category)
        return Spider_BaseClass.AllProductUrls

    def listing(self, categorylink, category):
        CategoryLinkResponse = requests.get(categorylink, params={"countryCode": "US"},cookies=Spider_BaseClass.cookiesDict)
        categoryPageResponse = HtmlResponse(url=categorylink, body=CategoryLinkResponse.text, encoding='utf-8')
        product_list = categoryPageResponse.xpath("//h3[@class='card__title']/a/@href").extract()
        for productUrl in product_list:
            if not productUrl.startswith(store_url):
                productUrl = store_url.rstrip('/') + productUrl
            Spider_BaseClass.AllProductUrls.append(productUrl)
            # print(productUrl)
            siteMapCategory = str(Spider_BaseClass.ProductUrlsAndCategory.get(productUrl)).replace('None', '')
            if siteMapCategory:
                Spider_BaseClass.ProductUrlsAndCategory[productUrl] = siteMapCategory + " " + category
            else:
                Spider_BaseClass.ProductUrlsAndCategory[productUrl] = category
        try:
            nextpageUrl = \
                categoryPageResponse.xpath("//a[@rel='next']/@href").get()
            if not nextpageUrl.startswith(store_url):
                nextpageUrl = store_url.rstrip('/') + nextpageUrl
            self.listing(nextpageUrl, category)
        except:
            pass

    def GetProducts(self, response):
        ignorProduct = self.IgnoreProduct(response)
        if ignorProduct == True:
            self.ProductIsOutofStock(GetterSetter.ProductUrl)
        categoryAndName = self.GetCategory(response) + " " + self.GetName(response)
        if (re.search(r'\bNew Arrivals\b', categoryAndName, re.IGNORECASE) or
            re.search(r'\bBaby Clothes\b', categoryAndName, re.IGNORECASE)
            or re.search(r'\bSuits\b', categoryAndName, re.IGNORECASE)
            or re.search(r'\bBaby Clothes\b', categoryAndName, re.IGNORECASE)) and not \
                re.search(
                    r'\b((shirt(dress?)|jump(suit?)|dress|gown|set|footie|romper|footed pajama|overall|body(suit?)|suit|caftan)(s|es)?)\b',
                    categoryAndName,
                    re.IGNORECASE):
            print('Skipping Non Dress Product')
            self.ProductIsOutofStock(GetterSetter.ProductUrl)
        else:
            self.GetProductInfo(response)

    def GetName(self, response):
        color = self.GetSelectedColor(response)
        name = response.xpath("//h1[@class='product-view__title']/span/text()").get().strip()
        if not color == '' and not re.search(color, name):
            name = name + ' - ' + color
        return name

    def GetSelectedColor(self, response):
        try:
            color = str(
                response.xpath(
                    "//div[@class='value color']//li[contains(@class,'selectable selected')]/a/@title").get().strip()).replace(
                'Select Color:', '').title().strip()
        except:
            color = ''
        return color

    def GetPrice(self, response):
        orignalPrice = response.xpath(
            "//div[contains(@class,'price--varying-price')]/span[contains(@class,'price__from')]/following-sibling::span/text()").get()
        if orignalPrice != None:
            return float(str(orignalPrice).replace('$', '').replace(',', '').strip())
        else:
            regularPrice = response.xpath(
                "//div[contains(@class,'product-view__status')]/div/span[@class='price__current']/text()").get()
            return float(str(regularPrice).replace('$', '').replace(',', '').strip())

    def GetSalePrice(self, response):
        salePrice = response.xpath(
            "//div[contains(@class,'price--discount')]/span[contains(@class,'price__current')]/text()").get()
        if salePrice != None:
            return float(str(salePrice).replace("$", "").replace(',', '').strip())
        else:
            return 0

    def GetBrand(self, response):
        return response.xpath("//a[@class='product-view__brand']/text()").get()

    def GetImageUrl(self, response):
        imageUrls = []
        images = response.xpath("//button[contains(@class,'thumbnails__item')]/figure/img/@src").extract()
        if images:
            for image in images:
                print(image)
                imageUrls.append(str(image).replace('small', 'large'))
            return imageUrls
        else:
            raise NotImplementedError('NO Images Found')

    def GetDescription(self, response):
        description = ' '.join(response.xpath("//div[@class='tabccordion__description']/text()").extract()).replace(
            '\n', '').strip()
        composition = ' '.join(response.xpath("//div[@id='tab-product-specification']/text()").extract()).replace('\n',
                                                                                                                  '').strip()
        return description + " " + composition

    def GetSizes(self, response):
        productSizes = []
        colorName = self.GetSelectedColor(response)
        sizeOptions = response.xpath(
            "//ul[@class='product-sizes']/li/input")
        gender = ProductFilters.objects.get(ProductUrl=GetterSetter.ProductUrl).ParentCategory.split(',')[0]
        for sizeOption in sizeOptions:
            sizeOrignalPrice = sizeOption.xpath("./@data-value").get().strip()
            if sizeOrignalPrice != None:
                sizeOrignalPrice = float(str(sizeOrignalPrice).replace("$", "").replace(',', '').strip())
            else:
                sizeOrignalPrice = 0.0
            sizeName = sizeOption.xpath("./following-sibling::label/text()").get().strip()
            fitType = GetFitType(gender, sizeName)
            available = True
            sizelist = str(colorName), str(sizeName), available, str(fitType), sizeOrignalPrice, 0.0
            productSizes.append(sizelist)
        return productSizes

    def GetCategory(self, response):
        siteMapCategory = str(Spider_BaseClass.ProductUrlsAndCategory.get(GetterSetter.ProductUrl)).replace('None', '')
        return 'Baby ' + siteMapCategory

    def IgnoreProduct(self, response):
        if re.search('"availability":', response.text):
            productAvailability = response.text.split('"availability":')[1].split(',')[0].strip()
            if not 'InStock' in productAvailability:
                return True
            else:
                return False
