import sys
from pathlib import Path

DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(DIR.parent.parent.parent.parent))
__package__ = DIR.name

import django

django.setup()
from Shopify import *
from scrapy import signals

store_url = sys.argv[4]


class Chaserbrandscrapper(shopify):
    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(Chaserbrandscrapper, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        return spider

    def GetProductUrls(self, homePageResponse):
        # ========== Category And Subcategory ==========#
        topCategoryNodes = homePageResponse.xpath(
            """//header//ul[@class='menu center']/div/li[a[contains(text(),'Shop All') or contains(text(),"What's New")]]""")
        for topCategoryNode in topCategoryNodes:
            topCategoryTitle = topCategoryNode.xpath("./a/text()").get().strip()
            topCategorylink = topCategoryNode.xpath("./a/@href").get().strip()
            data_dropdown_rel = topCategoryNode.xpath("./a/@data-dropdown-rel").get().strip()
            if not topCategorylink.startswith(store_url):
                topCategorylink = store_url.rstrip('/') + topCategorylink
            if topCategoryTitle == "What's New":
                categoryNodes = topCategoryNode.xpath("./ul/li/a[text()='Womens']")
                for categoryNode in categoryNodes:
                    categoryTitle = categoryNode.xpath("./text()").get().strip()
                    categorylink = categoryNode.xpath("./@href").get()
                    if not categorylink.startswith(store_url):
                        categorylink = store_url.rstrip('/') + categorylink
                    category = topCategoryTitle + " " + categoryTitle
                    self.listing(categorylink, category)
            else:
                categoryNodes = homePageResponse.xpath(
                    "//div[@data-dropdown='" + data_dropdown_rel + "']//ul[@class='dropdown_title']/li[a[contains(text(),'Shop Women') or contains(text(),'Shop Girls') or contains(text(),'Shop Men') or contains(text(),'Shop Boys') ]]")
                for categoryNode in categoryNodes:
                    categoryTitle = categoryNode.xpath("./a/text()").get().strip()
                    categorylink = categoryNode.xpath("./a/@href").get()
                    gender = categoryTitle.replace("Shop ", '').strip()
                    subCategoryNodes = categoryNode.xpath(
                        "./../following-sibling::ul/li[a[contains(text(),'Dresses')]]")
                    for subCategoryNode in subCategoryNodes:
                        subCategoryTitle = subCategoryNode.xpath("./a/text()").get().strip()
                        subCategorylink = subCategoryNode.xpath("./a/@href").get()
                        if not subCategorylink.startswith(store_url):
                            subCategorylink = store_url.rstrip('/') + subCategorylink
                        category = gender + " " + topCategoryTitle + " " + categoryTitle + " " + subCategoryTitle
                        self.listing(subCategorylink, category)
        return Spider_BaseClass.AllProductUrls

    def listing(self, categorylink, category):
        categoryLinkResponse = requests.get(categorylink)
        categoryLinkResponse = HtmlResponse(url=categorylink, body=categoryLinkResponse.text, encoding='utf-8')
        product_list = categoryLinkResponse.xpath("//div[@class='collections-wishlist-block']/a/@href").extract()
        for productUrl in product_list:
            if not productUrl.startswith(store_url):
                productUrl = store_url.rstrip('/') + productUrl
            productUrl = self.GetCanonicalUrl(productUrl)
            Spider_BaseClass.AllProductUrls.append(productUrl)
            siteMapCategory = str(Spider_BaseClass.ProductUrlsAndCategory.get(productUrl)).replace('None', '')
            if siteMapCategory:
                Spider_BaseClass.ProductUrlsAndCategory[productUrl] = siteMapCategory + " " + category
            else:
                Spider_BaseClass.ProductUrlsAndCategory[productUrl] = category
        try:
            nextPageUrl = categoryLinkResponse.xpath("//link[@rel='next']/@href").extract()[0]
            if not nextPageUrl.startswith(store_url):
                nextPageUrl = store_url.rstrip('/') + nextPageUrl
            self.listing(nextPageUrl, category)
        except:
            pass

    def GetProducts(self, response):
        ignorProduct = self.IgnoreProduct(response)
        if ignorProduct == True:
            self.ProductIsOutofStock(GetterSetter.ProductUrl)
        shopify.productJson = json.loads(self.SetProductJson(response))
        categoryAndName = shopify.GetCategory(self, response) + " " + self.GetName(response)

        if re.search(r'\b' + 'New in' + r'\b', categoryAndName, re.IGNORECASE) and not re.search(
                r'\b((shirt(dress?)|jump(suit?)|dress|gown|romper|suit|caftan|Treats|)(s|es)?)\b', categoryAndName,
                re.IGNORECASE):
            print('Skipping Non Dress Product')
            self.ProductIsOutofStock(GetterSetter.ProductUrl)
        else:
            self.GetProductInfo(response)

    def GetName(self, response):
        productId = ''
        if re.search('"productId"', response.text):
            productId = str(response.text.split('"productId":')[1].split(',"')[0])
        name = shopify.GetName(self, response)
        if not productId == '' and not re.search(productId, name):
            name = name + ' - ' + productId
        return name

    def IgnoreProduct(self, response):
        if re.search('"availability":', response.text):
            productAvailability = response.text.split('"availability":')[1].split(',')[0].strip()
            if not 'InStock' in productAvailability:
                return True
            else:
                return False
