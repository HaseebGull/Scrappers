from BaseClass import *
from scrapy import signals
from WebDriver import SeleniumResponse

DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(DIR.parent.parent.parent.parent))
__package__ = DIR.name

import django

django.setup()

store_url = sys.argv[4]


class HarrodsScrapper(Spider_BaseClass):
    Spider_BaseClass.cookiesDict = {"currency": "USD", "currencyOverride": "USD"}
    Spider_BaseClass.hasDriver = True

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(HarrodsScrapper, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        return spider

    def GetProductUrls(self, response):
        category_json = '[{"title":"Designers"' + \
                        str(response.text).split('[{"title":"Designers"')[1].split(',"type":"Group"}]}}}')[
                            0] + ',"type":"Group"}]'
        category_json = json.loads(category_json)
        for top_category in category_json:
            top_category_name = top_category['title']
            list = ['Women', 'Kids', 'Men']
            if not Enumerable(list).where(lambda x: x in top_category_name).first_or_default():
                continue
            print('topo_cat_name :', top_category_name)
            category_nodes = top_category['children']
            for category_node in category_nodes:
                for category_node1 in category_node['children']:
                    category_name = category_node1['title']
                    list2 = ['Clothing', 'Girls', 'Boys']
                    if not Enumerable(list2).where(lambda x: x in category_name).first_or_default():
                        continue
                    print("Cat_name :", category_name)
                    sub_category_nodes = category_node1['children']
                    for sub_category_node in sub_category_nodes:
                        sub_category_name = sub_category_node['title']
                        list3 = ['Dresses', 'Nightwear', 'Knitwear', 'Suits', 'Sportswear', 'Trousers', 'Rompers']
                        if not Enumerable(list3).where(lambda x: x in sub_category_name).first_or_default():
                            continue
                        sub_category_link = sub_category_node['link']['url']
                        if not sub_category_link.startswith(store_url):
                            storeurl = store_url.split('/en-us')[0]
                            sub_category_link = storeurl + sub_category_link
                        print(sub_category_name, " :", sub_category_link)
                        category = top_category_name + " " + category_name + " " + sub_category_name
                        self.listing(sub_category_link,category)
        return Spider_BaseClass.AllProductUrls
    def listing(self,sub_category_link,category):
        collectionName = sub_category_link.split("/")[-1]
        api_url= 'https://www.harrods.com/api/commerce/v1/listing/women-clothing-dresses?icid=megamenu_shop_women_clothing_dresses&pageindex=1'
        responeapi = requests.get(url=api_url, timeout=6000)
        apiresponse = json.loads(responeapi.content)
        page_no = 2
        total_pages = apiresponse['products']['totalPages']
        while page_no <= int(total_pages):
            page_no += 1
            product_list = apiresponse['products']['entries']
            for product_url in product_list:
                product_url = product_url['slug']
                if not product_url.startswith(store_url):
                    product_url = store_url.rstrip('/') + product_url
                print("Product-Url :", product_url)
                Spider_BaseClass.AllProductUrls.append(product_url)
                siteMapCategory = str(Spider_BaseClass.ProductUrlsAndCategory.get(product_url)).replace('None', '')
                if siteMapCategory:
                    Spider_BaseClass.ProductUrlsAndCategory[product_url] = siteMapCategory + " " + category
                else:
                    Spider_BaseClass.ProductUrlsAndCategory[product_url] = category
            try:
                api_url = 'https://www.harrods.com/api/commerce/v1/listing/' + str(collectionName) +'&pageindex=' + str(page_no)
                responeapi = requests.get(url=api_url, timeout=6000)
                apiresponse = json.loads(responeapi.content)
            except:
                pass