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


class Mclabelsscrapper(shopify):
    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(Mclabelsscrapper, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        return spider

    def GetProductUrls(self, homePageResponse):
        # ========== Category And Subcategory ==========#
        topCategoryNodes = homePageResponse.xpath(
            "//ul[contains(@class,'x-menu--level-1--container')]/li[a/span[contains(text(),'Women') or contains(text(),'Men')  or contains(text(),'SALE') ]]")
        for topCategoryNode in topCategoryNodes:
            topCategoryTitle = topCategoryNode.xpath("./a/span/text()").get().strip()
            topCategorylink = topCategoryNode.xpath("./a/@href").get()
            if not topCategorylink.startswith(store_url):
                topCategorylink = store_url.rstrip('/') + topCategorylink
            print("TOP CATEGORY  :", topCategoryTitle, " : TOP CATEGORY LINK  :", topCategorylink)
            categoryNodes = topCategoryNode.xpath(
                "./div/ul/li[a[contains(text(),'Clothing') or contains(text(),'Sale Man')or contains(text(),'Sale Woman')]]")
            for categoryNode in categoryNodes:
                categoryTitle = categoryNode.xpath("./a/text()").get().strip()
                categorylink = categoryNode.xpath("./a/@href").get()
                if not categorylink.startswith(store_url):
                    categorylink = store_url.rstrip('/') + categorylink
                print("CATEGORY  :", categoryTitle, " : CATEGORY LINK  :", categorylink)
                subcategoryNodes = categoryNodes.xpath(
                    "./ul/li/a[contains(text(),'Dresses') or contains(text(),'Jumpsuits') or contains(text(),'Suits') or contains(text(),'Clothing')]")
                for subcategoryNode in subcategoryNodes:
                    subcategoryTitle = subcategoryNode.xpath("./text()").get().strip()
                    subcategorylink = subcategoryNode.xpath("./@href").get()
                    if not subcategorylink.startswith(store_url):
                        subcategorylink = store_url.rstrip('/') + subcategorylink
                    print("SUB_CATEGORY  :", subcategoryTitle, ": SUB_CATEGORY LINK  :", subcategorylink)

                    if re.search('\?', subcategorylink):
                        subcategorylink = 'https' + subcategorylink.split('https' or 'http')[1].split('?')[0].strip()
                    # ==================================== BREADCRUM ================================= #
                    category = topCategoryTitle + " " + categoryTitle + " " + subcategoryTitle
                    print("BreadCrum : ", category)
                    # ====================================  ================================= #
                    self.listing(subcategorylink, category)
        return Spider_BaseClass.AllProductUrls

    def listing(self, subcategorylink, category):
        categoryPageResponse = requests.get(subcategorylink)
        categoryPageResponse = HtmlResponse(url=subcategorylink, body=categoryPageResponse.text,
                                            encoding='utf-8')
        product_list = categoryPageResponse.xpath("//a[div[contains(@class,'product--image')]]/@href").extract()
        for productUrl in product_list:
            if not productUrl.startswith(store_url):
                productUrl = store_url.rstrip('/') + productUrl
            productUrl = self.GetCanonicalUrl(productUrl)
            print('prod url link :', productUrl)
            Spider_BaseClass.AllProductUrls.append(productUrl)
            siteMapCategory = str(Spider_BaseClass.ProductUrlsAndCategory.get(productUrl)).replace('None', '')
            if siteMapCategory:
                Spider_BaseClass.ProductUrlsAndCategory[productUrl] = siteMapCategory + " " + category
            else:
                Spider_BaseClass.ProductUrlsAndCategory[productUrl] = category
        try:
            nextpage = categoryPageResponse.xpath("//link[@rel='next']/@href").extract()[0]
            if not nextpage.startswith(store_url):
                nextpage = store_url.rstrip('/') + nextpage
            print("NEXTPAGE URL :", nextpage)
            nextpageresponse = requests.get(nextpage)
            nextpageresponse = HtmlResponse(url=nextpage, body=nextpageresponse.text, encoding='utf-8')
            self.listing(nextpageresponse, category)
        except:
            pass

    def IgnoreProduct(self, response):
        productAvailability = response.xpath("//link[@itemprop='availability']/@href").get()
        if 'InStock' in productAvailability:
            return False
        else:
            return True

    def GetSizes(self, response):
        sizes = shopify.GetSizes(self, response)
        sizeList = []
        for size in sizes:
            print(str(size).replace('-', ''))
            mappedSize = size[1]
            MappedSize = size[0], mappedSize, size[2], size[3], size[4], size[5]
            sizeList.append(MappedSize)
        return sizeList

    def GetCategory(self, response):
        filterList = []
        if GetterSetter.ProductUrl in Spider_BaseClass.ProductUrlsAndCategory:
            categories = Spider_BaseClass.ProductUrlsAndCategory[GetterSetter.ProductUrl]
            for category in str(categories).split('$'):
                filterList.append(category)

        for filter in shopify.productJson['tags']:
            filterList.append(filter)
        filters = '$'.join(map(str, filterList))
        return "Women " + filters
