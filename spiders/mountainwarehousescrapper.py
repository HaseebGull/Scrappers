from BaseClass import *
from scrapy import signals

DIR = Path(__file__).resolve().parent

sys.path.insert(0, str(DIR.parent.parent.parent.parent))
__package__ = DIR.name

django.setup()

store_url = sys.argv[4]


class MountainwarehouseScrapper(Spider_BaseClass):
    Spider_BaseClass.cookiesDict = {"currency": "USD", "currencyOverride": "USD"}

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(MountainwarehouseScrapper, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        return spider

    def GetProductUrls(self, response):
        topCategoryNodes = response.xpath(
            "//div[@class='c-header-nav__body']/ul/li[a[contains(text(),'Womens') or "
            "contains(text(),'Kids')]]")
        for top_category_node in topCategoryNodes:
            top_category_title = top_category_node.xpath("./a/text()").get().strip()
            print("TOP CATEGORY  :", top_category_title)
            category_nodes = top_category_node.xpath(".//div/ul/li[a[contains(text(),'Dresses') or contains(text(),"
                                                     "'Babywear') or contains(text(),'Plus') or contains(text(),"
                                                     "'Tops')]]")
            for category_node in category_nodes:
                category_title = category_node.xpath('./a/text()').get().strip()
                print("category :", category_title)
                sub_category_nodes = category_node.xpath("./ul/li/a[contains(text(),'Sweaters') or contains(text(),"
                                                         "'Dresses') or contains(text(),'Clothing')]")
                for sub_category_node in sub_category_nodes:
                    sub_category_title = sub_category_node.xpath("./text()").get().strip()
                    sub_category_link = sub_category_node.xpath("./@href").get()
                    if not sub_category_link.startswith(store_url):
                        storeurl = store_url.split('/us')[0]
                        sub_category_link = storeurl.rstrip('/') + sub_category_link
                    print(sub_category_title, " :", sub_category_link)
                    category = top_category_title + " " + category_title + " " + sub_category_title
                    self.listing(sub_category_link, category)
        return Spider_BaseClass.AllProductUrls

    def listing(self, sub_category_link, category):
        CategoryLinkResponse = requests.get(sub_category_link)
        sub_category_pageresponse = HtmlResponse(url=sub_category_link, body=CategoryLinkResponse.text,
                                                 encoding='utf-8')
        product_list_josn = '{"categoryModel":{' + str(sub_category_pageresponse.text).split('{"categoryModel":{')[1].split('), document.getElementById')[0]
        product_list_josn = json.loads(product_list_josn)
        product_list = product_list_josn['categoryModel']['CategoryData']['Products']
        for product_info in product_list:
            product_url = product_info['BaseUrl']
            color = product_info['Colour']
            if not product_url.startswith(store_url):
                storeurl = store_url.split('/us')[0]
                product_url = (storeurl.rstrip('/') + '/' + product_url + "/" + color)
            print("PRODUCT URL :", product_url)
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
        name = str(response.xpath("//h1[@itemprop='name']/text()").get()).strip()
        if not color == '' and not re.search(color, name, re.I):
            name = name + " - " + color
        print("name =", name)
        return name

    def GetSelectedColor(self, response):
        color = str(response.url).split('aspx/')[1].split('/')[0]
        return color

    def GetPrice(self, response):
        orignalPrice = response.xpath(
            "//span[contains(@class,'linethrough')]/text()").get()
        if orignalPrice != None:
            return float(str(orignalPrice).strip().replace('$', '').replace(',', ''))
        else:
            regularPrice = response.xpath(
                "//span[contains(@class,'linethrough')]/text()").get()
            return float(str(regularPrice).strip().replace('$', '').replace(',', ''))

    def GetSalePrice(self, response):
        salePrice = response.xpath(
            "//span[contains(@class,'price-label')]/text()").get()
        if salePrice != None:
            return float(str(salePrice).strip().replace('$', '').replace(',', ''))
        else:
            return 0

    def GetBrand(self, response):
        return str(response.xpath("//a[contains(@class,'product-partner')]/text()").get()).strip()

    def GetImageUrl(self, response):
        imageUrls = []
        color = self.GetSelectedColor(response)
        json_str = '{"Contains360Image"' + str(response.text).split(r'"Contains360Image"')[1].split(r',"Videos"')[0] + '}'
        image_json = json.loads(json_str)
        for image in image_json['Images']:
            image_text = str(image['ImageAltText']).lower()
            if color == image_text:
                imageUrl = image['ImageUrl']
                imageUrls.append(imageUrl)
        return imageUrls

    def GetDescription(self, response):
        return ' '.join(response.xpath("//div[@itemprop='description']//text()").extract()).strip()

    def GetSizes(self, response):
        sizes = []
        color = self.GetSelectedColor(response)
        print("COLOR SIZE :",color)
        gender = ProductFilters.objects.get(ProductUrl=GetterSetter.ProductUrl).ParentCategory.split(',')[0]
        json_str = '{"KitDisplayComponents"' + str(response.text).split(r'{"KitDisplayComponents"')[1].split(r',"Contains360Image"')[0] +'}'
        size_json = json.loads(json_str)
        for size_list in size_json["Options"]:
            product_color = str(size_list["ColourName"]).lower()
            if color == product_color:
                avalaible_stock = size_list["StockCount"]
                size_name = size_list["SizeName"]
                print(" SIZES :" , size_name)
                if avalaible_stock != 0:
                    sizes.append((color, size_name, gender, 0.0, 0.0))
        return sizes
    def GetCategory(self, response):
        return "Women " + str(Spider_BaseClass.ProductUrlsAndCategory.get(GetterSetter.ProductUrl)).replace('None', '')
