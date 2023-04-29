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


class BodenusaScrapper(Spider_BaseClass):
    product_json = ''
    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(BodenusaScrapper, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        return spider

    def GetProductUrls(self, response):
        category_nodes = response.xpath("(//ul[@class='nav-rd']/li[a/span[not(contains(text(),'VACATION'))]])[1]")
        for category_node in category_nodes:
            category_title = category_node.xpath("./a/span/text()").get().strip()
            print("TOP CATEGORY  :", category_title)
            # //ul[@class='nav-rd']/li[a/span[not(contains(text(),'VACATION'))]]//div[contains(@class,'menuItem')]/div[a/span[contains(text(),"Jeans")]]
            sub_category_nodes = category_node.xpath("(.//div[contains(@class,'menuItem')]/div[a/span[contains(text(),"
                                                     "'Dresses') or contains(text(),'New') or contains(text(),"
                                                     "'Loungewear') or contains(text(),'Sweaters') or contains(text(),"
                                                     "'Petite') or contains(text(),'suits') or contains(text(),"
                                                     "'Knit') or contains(text(),'Rompers')]])[1]")
            for sub_category_node in sub_category_nodes:
                sub_category_title = sub_category_node.xpath("./a/span/text()").get().strip()
                sub_category_link = sub_category_node.xpath("./a/@href").get()
                if not sub_category_link.startswith(store_url):
                    sub_category_link = store_url.rstrip('/') + sub_category_link
                print(sub_category_title, " :", sub_category_link)
                category = category_title + " " + sub_category_title
                self.listing(sub_category_link, category)
        return Spider_BaseClass.AllProductUrls

    def listing(self, subCategorylink, category):
        CategoryLinkResponse = requests.get(subCategorylink)
        subCategoryLinkResponse = HtmlResponse(url=subCategorylink, body=CategoryLinkResponse.text, encoding='utf-8')
        product_list = subCategoryLinkResponse.xpath("(//a[@class='product-item-link']/@href)[1]").extract()
        for productUrl in product_list:
            if not productUrl.startswith(store_url):
                productUrl = store_url.rstrip('/') + productUrl
            print('PRODUCT URL :', productUrl)
            Spider_BaseClass.AllProductUrls.append(productUrl)
            siteMapCategory = str(Spider_BaseClass.ProductUrlsAndCategory.get(productUrl)).replace('None', '')
            if siteMapCategory:
                Spider_BaseClass.ProductUrlsAndCategory[productUrl] = siteMapCategory + " " + category
            else:
                Spider_BaseClass.ProductUrlsAndCategory[productUrl] = category
        # try:
        #     nextPageUrl = subCategoryLinkResponse.xpath("//link[@rel='next']/@href").get()
        #     if not nextPageUrl.startswith(store_url):
        #         nextPageUrl = store_url.rstrip('/') + nextPageUrl
        #         print("NEXT PAGE :", nextPageUrl)
        #     self.listing(nextPageUrl, category)
        # except:
        #     pass

    def GetProducts(self, response):
        ignorProduct = self.IgnoreProduct(response)
        size_josn_str = '{"styleCode"' + response.text.split('{"styleCode"')[1].split('={styleCode}"}}')[0].strip() + '={styleCode}"}}'
        self.product_json = json.loads(size_josn_str)
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
        name = str(response.xpath("//span[contains(@class,'title__main')]/text()").get()).strip()
        if not color == '' and not re.search(color, name, re.I):
            name = name + " - " + color
        print("name =", name)
        return name

    def GetSelectedColor(self, response):
        color = str(response.xpath("//span[contains(@class,'title__sub')]/text()").get()).strip()
        return color

    def GetPrice(self, response):
        edp = self.product_json['options'][0]['skus'][0]['edp']
        style_code = self.product_json['styleCode']
        price_apI_url = self.product_json['_metadata']['priceApiUrl']
        api_url = str(price_apI_url).replace('{currency}', 'USD')
        responeapi = requests.get(url=api_url, timeout=6000)
        price_json = json.loads(responeapi.content)
        original_price = price_json[style_code]['prices']
        for original_price in original_price:
            cur_edp = original_price['edp']
            if cur_edp==edp:
                original_price = original_price['cataloguePrice']
                break
        if original_price is not None:
            return float(str(original_price).strip().replace('$', '').replace(',', '').replace('USD', ''))
        else:
            regularPrice = price_json[style_code]['prices']
            for regularPrice in regularPrice:
                cur_edp = regularPrice['edp']
                if cur_edp == edp:
                    original_price = original_price['cataloguePrice']
            return float(str(regularPrice).strip().replace('$', '').replace(',', '').replace('USD', ''))

    def GetSalePrice(self, response):
        edp = self.product_json['options'][0]['skus'][0]['edp']
        style_code = self.product_json['styleCode']
        price_apI_url = self.product_json['_metadata']['priceApiUrl']
        api_url = str(price_apI_url).replace('{currency}', 'USD')
        responeapi = requests.get(url=api_url, timeout=6000)
        price_json = json.loads(responeapi.content)
        salePrice = price_json[style_code]['prices']
        for salePrice in salePrice:
            cur_edp = salePrice['edp']
            if cur_edp == edp:
                salePrice = salePrice['sellingPrice']
                break
        if salePrice is not None:
            return float(str(salePrice).strip().replace('$', '').replace(',', '').replace('USD', ''))
        else:
            return 0

    def GetDescription(self, response):
        return ' '.join(
            response.xpath("//div[contains(@id,'accordion')]/div//text()").extract()).strip()

    def GetBrand(self, response):
        return "Booden"

    def GetSizes(self, response):
        sizes = []
        color = self.GetSelectedColor(response)
        stock_api_url = self.product_json['_metadata']['stockApiUrl']
        stock_api_response = requests.get(url=stock_api_url, timeout=6000)
        size_json = json.loads(stock_api_response.content)
        style_code = self.product_json['styleCode']
        for prod_info in self.product_json['options'][0]['skus']:
            prod_edp = prod_info['edp']
            for stock in size_json[style_code]:
                stock_edp = stock['edp']
                if prod_edp == stock_edp:
                    stock_info = stock['stockStatus']
                    if stock_info == 'InStock':
                        sizename = prod_info['sizeDescription']
                        available = True
                        fitType = prod_info['sizeGroup']
                        sizes.append((color, sizename, available, fitType, 0.0, 0.0))
        return sizes

    def GetImageUrl(self, response):
        imageUrls = []
        image_nodes = response.xpath(
            "//div[contains(@class,'zoom__img')]//img")
        for image in image_nodes:
            umage_url = image.xpath("./@src").get()
            imageUrls.append(umage_url)
        return imageUrls

    def GetCategory(self, response):
        siteMapCategory = str(Spider_BaseClass.ProductUrlsAndCategory.get(GetterSetter.ProductUrl)).replace('None', '')
        return "Women " + siteMapCategory
