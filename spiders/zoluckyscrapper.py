from BaseClass import *
from scrapy import signals

DIR = Path(__file__).resolve().parent

sys.path.insert(0, str(DIR.parent.parent.parent.parent))
__package__ = DIR.name

django.setup()

store_url = sys.argv[4]


class ZoluckyScrapper(Spider_BaseClass):
    Spider_BaseClass.cookiesDict = {"currency": "USD", "currencyOverride": "USD"}

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(ZoluckyScrapper, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        return spider

    def GetProductUrls(self, response):
        category_json = '[{"link_type":"collection","custom_link":null,"link":"/collections/new-in","name":"NEW"' + \
                        str(response.text).split(
                            '"link_type":"collection","custom_link":null,"link":"/collections/new-in","name":"NEW"')[
                            1].split('"summer-sale-2022"},"specific":[],"blog":[]}]')[
                            0] + '"summer-sale-2022"},"specific":[],"blog":[]}]'
        category_json = json.loads(category_json)
        for top_category in category_json:
            top_category_name = top_category['name']
            list = ['DRESSES', 'NEW', 'EARLY FALL', 'PLUS SIZE', 'SALE']
            if not Enumerable(list).where(lambda x: x in top_category_name).first_or_default():
                continue
            print('topo_cat_name :', top_category_name)
            category_nodes = top_category['children']
            for category_node in category_nodes:
                category_name = category_node['name']
                list2 = ["New In Days", 'Shop By Recommend', 'Special Offer', 'Shop By Price']
                if Enumerable(list2).where(lambda x: x in category_name).first_or_default():
                    continue
                print("Cat_name :", category_name)
                sub_category_nodes = category_node['children']
                for sub_category_node in sub_category_nodes:
                    sub_category_name = sub_category_node['name']
                    list3 = ['Tops', 'T-Shirts', 'Hoodies', 'Bottoms', 'Shoes', 'Accessories', 'Jacket & Cardigans',
                             'Blouses & Shirts Sale', 'Outerwear Sale', 'Acc Sale', 'T-shirt', 'Blouse&shirts',
                             'Bottms', 'T-shirts Sale ']
                    if Enumerable(list3).where(lambda x: x in sub_category_name).first_or_default():
                        continue
                    sub_category_link = sub_category_node['link']
                    if not sub_category_link.startswith(store_url):
                        sub_category_link = store_url + sub_category_link
                    print(sub_category_name, " :", sub_category_link)
                    category = top_category_name + " " + category_name + " " + sub_category_name
                    self.listing(sub_category_link, category)
        return Spider_BaseClass.AllProductUrls

    def listing(self, sub_category_link, category):
        CategoryLinkResponse = requests.get(sub_category_link)
        categoryPageResponse = HtmlResponse(url=sub_category_link, body=CategoryLinkResponse.text, encoding='utf-8')
        self.get_urls(sub_category_link, category)
        try:
            total_products = categoryPageResponse.xpath("//span[@class='notranslate']/text()").get().strip()
            print("Total prod =", total_products)
            if int(total_products) % 48 == 0:
                totalPages = int(total_products) / 48
            else:
                totalPages = int(total_products) / 48 + 1
            totalPages = str(totalPages).split('.')[0]
            print("total ", totalPages)
            page = 2
            while page <= int(totalPages):
                next_page_url = sub_category_link + "?page=" + str(page)
                print("NEXT  =", next_page_url)
                self.get_urls(next_page_url, category)
                page += 1
        except:
            pass

    def get_urls(self, sub_category_link, category):
        CategoryLinkResponse = requests.get(sub_category_link)
        categoryPageResponse = HtmlResponse(url=sub_category_link, body=CategoryLinkResponse.text, encoding='utf-8')
        product_nodes = categoryPageResponse.xpath(
            "//div[contains(@class,'product-item-info-content')]//a/@href").extract()
        for product_url in product_nodes:
            if not product_url.startswith(store_url):
                product_url = store_url + product_url
            print("URL =", product_url)
            Spider_BaseClass.AllProductUrls.append(product_url)
            siteMapCategory = str(Spider_BaseClass.ProductUrlsAndCategory.get(product_url)).replace('None', '')
            if siteMapCategory:
                Spider_BaseClass.ProductUrlsAndCategory[product_url] = siteMapCategory + " " + category
            else:
                Spider_BaseClass.ProductUrlsAndCategory[product_url] = category

    def GetProducts(self, response):
        if Spider_BaseClass.hasDriver:
            response = SeleniumResponse(response.url)
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
        name = str(response.xpath("//h1[contains(@class,'title')]/text()").get()).strip()
        if not color == '' and not re.search(color, name, re.I):
            name = name + " - " + color
        print("name =", name)
        return name

    def GetSelectedColor(self, response):
        color = str(response.xpath("//p[contains(text(),'Color')]/following-sibling::p/text()").get()).strip()
        return color

    def GetPrice(self, response):
        orignalPrice = response.xpath(
            "//p[contains(@class,'detail-price')]/following-sibling::p/text()").get()
        if orignalPrice != None:
            return float(str(orignalPrice).strip().replace('$', '').replace(',', ''))
        else:
            regularPrice = response.xpath("//p[contains(@class,'detail-price')]/text()").get()
            return float(str(regularPrice).strip().replace('$', '').replace(',', ''))

    def GetSalePrice(self, response):
        salePrice = response.xpath(
            "//p[contains(@class,'detail-price')]/text()").get()
        if salePrice != None:
            return float(str(salePrice).strip().replace('$', '').replace(',', ''))
        else:
            return 0

    def GetBrand(self, response):
        return "zolucky"

    def GetImageUrl(self, response):
        imagelist = []
        image_json = '[{"image":' + str(response.text).split('"images":[{"image":')[1].split(',"compare_at_price":')[0]
        image_json = json.loads(image_json)
        for imageUrls in image_json:
            image = imageUrls["image"]
            imageurl = "https://zolucky.com/image/" + image
            print("image url ", imageurl)
            imagelist.append(imageurl)
        return imagelist

    def GetDescription(self, response):
        return ' '.join(
            response.xpath("//div[contains(@class,'goods-detail-text')]//p/span/text()").extract()).strip()

    def GetSizes(self, response):
        sizes = []
        sizeList = response.xpath("//div[contains(@class,'flex-wrap gap-3')]/div/span")
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
