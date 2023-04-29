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


class NeimanMarcusScrapper(Spider_BaseClass):
    Spider_BaseClass.headersDict = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:98.0) Gecko/20100101 Firefox/98.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Cookie": "AMCV_5E85123F5245B3520A490D45%40AdobeOrg=-330454231%7CMCMID%7C11719004164054907450631480200681626676%7CMCIDTS%7C19066%7CMCAID%7CNONE%7CMCOPTOUT-1647245759s%7CNONE%7CMCAAMLH-1647843359%7C3%7CMCAAMB-1647843359%7Cj8Odv6LonN4r3an7LhD3WZrU1bUpAkFkkiY1ncBR96t2PTI%7CMCCIDH%7C-1579927318%7CMCSYNCSOP%7C411-19073%7CvVersion%7C3.1.2; TLTSID=30BB1456A35E10A3D0199FA4F6F272AE; TLTUID=30BB1456A35E10A3D0199FA4F6F272AE; JSESSIONID=n_pErbcXOUxNHB-Oyz1YsTbv434-mOcrGUGpWWZe.jsession; dt_personalize_data=%7B%22lastUpdatedDate%22%3A%22Mon+Mar+14+01%3A15%3A48+CDT+2022%22%2C%22bestCustomer%22%3A%22n%22%2C%22plcc%22%3A%22n%22%2C%22customerJourneySegment%22%3A%220%22%2C%22inCircleLevel%22%3A%220.0%22%2C%22promos%22%3A%5B%5D%2C%22customerScore%22%3A%220.0%22%2C%22emailSubscriber%22%3A%22n%22%7D; dt_favorite_store=""; tms_data={DT-2017.03}a3HwxssoiZzaMm5Pj2Bv6L13Gv8Ad/WZkJm2zLBiJ21pxbQQdoEBr+fVA6hUI02m+TAFrRCb4WARk7mTFM5Hjvy5TblWykM7/PUMuCENM8HOgb6AqRbmghZtcw0QnsW+SET4vqv0+h7lcA+ZxtQ8Uc3mG5P9J1Fx7g+Z+kfk4dLYWxi/HwIYIqJOzfAJkbiUnkKYCifwAXXPUn92L82ZzfwOGjJNVxHJr2yLnpU+PeiCV8YfXPAvnmWK1oI4vP8+lGthKWzKbYO3XE5bC/tNzryNVIMuUDWeCXzWohlXwSepqz0xUrGMT1LWu4MfuBvoIFqb78dpfsJza+LtVHrWlPgbq4PiKmK/3vRJC39ey2Oyuy11l5nCiwurrSXT8P3spXn+JLAdb2xxt+8hsgUWKZylw6Q2fwhDQFh3kzVcdCICZnEL2t//LDJ+yA4bDcXSziBd/75m+VboB1TNtXJrTZ7NrL9BqqTGGPT91qRv8kDhuVQVE2PjtzpDYCc8XyLHcoI/3bALhcBklxHcbInBNYLbyW7nyhHKcu2jVFSIEJdGvAaWPwydXccIztLojEQResTi/sf2NXktW2esM6D9hcxnSud1PY/ntGheGIuDAGfhXky1ZXPYxJUV1cn91hnsIDRhwBtn4bjWM7oO+Bxh0b7cK17WrAGmTWwi6/yu/w35OlOVnMdVVh3gD3EcDJMQiJt7J01X4HFCRRx8nCJuuH+XJOvHhb17frLIhjUFR1sO7pkd4ZOJ7nYHQu0b+MifaErNR4OWpEZI80NH56U3o/LqdxTlx9B6Ba8Bab1TFKR/zoCTl/KQ5qIk6zXORuM+EKPrYGY2i7KtFVcT9RURafE6q4OGUNNNu8uyjnnYC2vT1gUJp/NjhRdfZRvA8lPlj53MLuyLxWMZp6sxHMW3ybTOCv3bzbAZr6vKBY0GobsqC25h5jST4hOXpa1zJyzlAdMZx+98zBYHmk7rYvxhDQ==; WID=ff3685ea-5beb-41ed-be73-f1842ef0a55e; DYN_USER_ID=ff3685ea-5beb-41ed-be73-f1842ef0a55e; DYN_USER_CONFIRM=ae225bbce49b12b131e471168551efc7; W2A=3255631882.63065.0000; profile_data=%7B%22firstName%22%3A%22%22%2C%22currencyPreference%22%3A%22PKR%22%2C%22countryPreference%22%3A%22PK%22%2C%22securityStatus%22%3A%22Anonymous%22%2C%22cartItemCount%22%3A0%7D; SPCR=1; _cplid=1647238548204654; _optuid=1647238548204175; mbox=undefined; _optanalytics=nmsw0004%3Aa; dtCookie=v_4_srv_11_sn_004106BC23F01DE27D3A770C0FAC415C_perc_100000_ol_0_mul_1_app-3Aa8bc3ee5e9259c56_1; _pxhd=5JXZg5J1WLkumg85cbtKOd-JXyGtwHPgJBpldPFvprc6o7loHx3yBtwpxp0BkyZI8QlPLJH6r/GgKbDrahYiUg==:G8vOTXw9QZb/Lnt0spNkztFtPMiip2369MzQKoLOa-iBROZ4nzA3U/kKMEeMxmoFReTBiZSZR/mWUFaJZU7hxgCQZ8sMqI0TFH7PoU/tI6k=; rxVisitor=16472385538470EAERVNP45CSOA1K74D8DR2N2E642GUC; dtPC=11$238553834_251h-vPCAHMHKKKMQRFDQMRCQKUWTTEKSFSVHG-0; rxvt=1647240486177|1647238553854; cacheBustKey=1647238555095; _px2=eyJ1IjoiMzUxNzVlNjAtYTM1ZS0xMWVjLTlhOWEtZTUwZWQ4YTlkNzM5IiwidiI6IjMwOTZlNzczLWEzNWUtMTFlYy1iYzk3LTUwNjU0ODZjNDY2OSIsInQiOjE2NDcyMzg4NTQ3MjcsImgiOiIzZGJiMzc0ZDNjZGNkZjM2MWYxYjg2ZGZhMGI2ZDBmNzk5MzdmZGQyMmM4NDkzMDMyOTcyMzRjNWQ5ZTllYjQyIn0=; pxcts=32843e94-a35e-11ec-976b-54704e547a6f; _pxvid=3096e773-a35e-11ec-bc97-5065486c4669; revisitUser=true; cookieConsent=true; dtSa=-; dtLatC=34; load_times=4.78_17.53; utag_main=v_id:017f8711b18c0022b2eae5b608720004e002300d0086e$_sn:1$_ss:0$_st:1647240361074$ses_id:1647238558094%3Bexp-session$_pn:1%3Bexp-session$vapi_domain:neimanmarcus.com$_prevpage:Homepage%3Bexp-1647242159374$dc_visit:1$dc_event:1%3Bexp-session$dc_region:eu-central-1%3Bexp-session; dt_gender_placement=undefined; wlcme=true; _uetsid=36f377c0a35e11ec988407c79066c12e; _uetvid=36f37220a35e11eca2c13390a1795c66; s_ecid=MCMID%7C11719004164054907450631480200681626676; AMCVS_5E85123F5245B3520A490D45%40AdobeOrg=1; xyz_cr_1027_et_111=; pt_ck=home; s_vnum=1648753200378%26vn%3D1; s_invisit=true; s_ppv=https%253A%2F%2Fwww.neimanmarcus.com%2Fen-pk%2F%2C12%2C12%2C278; s_tp=2408; _svsid=4a85431ffbaa5f6a93eaf3b50de25556; CChipCookie=2097217546.61525.0000; TS01bbdfeb=01d3b151d54143cb77ea245a654bf459055b6bf7d93986bb40d0843613f194f55c8dbff4701034c2b72a26a97afdab82ba429fccc1; TS01fabb3d=01d3b151d54143cb77ea245a654bf459055b6bf7d93986bb40d0843613f194f55c8dbff4701034c2b72a26a97afdab82ba429fccc1; mp_neiman_marcus_mixpanel=%7B%22distinct_id%22%3A%20%2217f8711b7294ac-03d9f6e1d572a18-4c3e2d72-100200-17f8711b72a34d%22%2C%22bc_persist_updated%22%3A%201647238559532%7D; _gcl_au=1.1.441150740.1647238560; _mibhv=anon-1647238559800-1139829699_6982; _br_uid_2=uid%3D8710781000819%3Av%3D11.8%3Ats%3D1647238559987%3Ahc%3D2; br_ab=A; br_df=D; s_cc=true; _evga_e287=ff3685ea-5beb-41ed-be73-f1842ef0a55e.; _ga_1B8WTDSBDF=GS1.1.1647238559.1.0.1647238559.60; _ga=GA1.2.1371492290.1647238561; _pin_unauth=dWlkPU5UbGxPVEkyT0RFdE9EVTFNeTAwWkRoakxUZzVabVV0WWpjM09UVTROV1UyTkdNeg; bc_invalidateUrlCache_targeting=1647238561050; evg_recs=EVG; bluecoreNV=true; _svidobj={}; _clck=1vt5ugr|1|ezr|0; _gid=GA1.2.1583890866.1647238563; _clsk=1vsbwqx|1647238564232|1|0|k.clarity.ms/collect; _fbp=fb.1.1647238564331.1290852318; s_sq=nmgincglobalprod%3D%2526pid%253DHomepage%2526pidt%253D1%2526oid%253Dfunction%252528%252529%25257Bvarxb%25253Doa.replace%252528%252522on%252522%25252C%252522%252522%252529%25253Bja.bi%252528W%25252CDa%25252Cxb%25252B%252522wrapper%252522%252529%25253Bxb%25253Dnull%25253BTa%252526%252526%252528xb%25253Dta.actionCallback%252528Ta%25252Ct%2526oidt%253D2%2526ot%253DI; QuantumMetricSessionID=cc0486cf470019c9f8a0db137168b0f3; QuantumMetricUserID=cf386d14bb7acb6673dd0813f45f3809; _vid_t=SbbJyU+OkJofVlbOFm8Pg2Hn9XFzGCLca/IxFcBD2nf9Yr4Ma3quab27sqn964tVlFnGlgvcU0DrkA=="}

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(NeimanMarcusScrapper, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        return spider

    def GetProductUrls(self, homePageResponse):
        print(homePageResponse.text)
        # ========== Category And Subcategory ==========#
        topCategoryNodes = homePageResponse.xpath(
            "//nav[@id='silo-navigation']/ul/li/div[a[contains(span/text(),'Women') or contains(span/text(),'Men') or contains(span/text(),'Kids')]]")
        for topCategoryNode in topCategoryNodes:
            topCategoryTitle = topCategoryNode.xpath("./a/span/text()").get().strip()
            topCategorylink = topCategoryNode.xpath("./a/@href").get()
            if not topCategorylink.startswith(store_url):
                topCategorylink = store_url.rstrip('/') + topCategorylink
            categoryNodes = topCategoryNode.xpath(
                "./section/div/div/div[h6/a[contains(text(),'Clothing') or contains(text(),'Dress') or text()='Girls' or text()='Boys' or text()='Baby']]")
            for categoryNode in categoryNodes:
                categoryTitle = categoryNode.xpath("./h6/a/text()").get().strip()
                categorylink = categoryNode.xpath("./h6/a/@href").get()
                if not categorylink.startswith(store_url):
                    categorylink = store_url.rstrip('/') + categorylink
                    subCategoryNodes = categoryNode.xpath(
                        "/ul/li/a[contains(text(),'Dress') or contains(text(),'Jumpsuits') or contains(text(),'Suit') or contains(text(),'Tuxedos') or contains(text(),'Baby Girl') or contains(text(),'Baby Boy')]")
                    for subCategoryNode in subCategoryNodes:
                        subCategoryTitle = subCategoryNode.xpath("./text()").get().strip()
                        subCategorylink = subCategoryNode.xpath("./@href").get()
                        if not subCategorylink.startswith(store_url):
                            subCategorylink = store_url.rstrip('/') + subCategorylink
                        category = topCategoryTitle + " " + categoryTitle + " " + subCategoryTitle
                        print(category)
                        self.listing(subCategorylink, category)
        return Spider_BaseClass.AllProductUrls

    def listing(self, categorylink, category):
        categoryLinkResponse = requests.get(categorylink, stream=True)
        categoryLinkResponse = HtmlResponse(url=categorylink, body=categoryLinkResponse.text, encoding='utf-8')
        product_list = categoryLinkResponse.xpath(
            "//a[contains(@class,'product-link')]/@href").extract()
        for productUrl in product_list:
            if not productUrl.startswith(store_url):
                productUrl = store_url.rstrip('/') + productUrl
            if re.search('https://', productUrl) and re.search('\?', productUrl):
                productUrl = 'https://' + productUrl.split('https://')[1].split('?')[0].strip()
            Spider_BaseClass.AllProductUrls.append(productUrl)
            siteMapCategory = str(Spider_BaseClass.ProductUrlsAndCategory.get(productUrl)).replace('None', '')
            if siteMapCategory:
                Spider_BaseClass.ProductUrlsAndCategory[productUrl] = siteMapCategory + " " + category
            else:
                Spider_BaseClass.ProductUrlsAndCategory[productUrl] = category
        try:
            pageNo = ''
            nextPage = categoryLinkResponse.xpath(
                "//a[@rel='next' and contains(@href, 'javascript:setPageNumber') and not(contains(@href, 'javascript:void(0);'))]/@href").get()

            if re.search('\(', str(nextPage)):
                pageNo = str(nextPage).split('(')[1].split(')')[0]

            if pageNo:
                if re.search('pageNum=', categorylink):
                    categorylink = categorylink.split('pageNum')[0].rstrip('? | &')
                if re.search('\?', categorylink):
                    nextPageUrl = categorylink + '&pageNum=' + str(pageNo) + ''
                else:
                    nextPageUrl = categorylink + '?pageNum=' + str(pageNo) + ''
                self.listing(nextPageUrl, category)
        except:
            pass

    def GetProducts(self, response):
        global productjson
        ignorProduct = self.IgnoreProduct(response)
        if ignorProduct == True:
            self.ProductIsOutofStock(GetterSetter.ProductUrl)
        else:
            self.GetProductInfo(response)

    def IgnoreProduct(self, response):
        if re.search('"availability":"', response.text):
            productAvailability = response.text.split('"availability":"')[1].split('"}}')[0].strip()
            if not 'InStock' in productAvailability or 'PreOrder' in productAvailability:
                return True
            else:
                return False

    def GetName(self, response):
        color = self.GetSelectedColor(response)
        name = str(response.xpath("//h1[contains(@class,'product-name')]/text()").get()).strip()
        if not color == '' and not re.search(color, name, re.I):
            name = name + " - " + color
        return name

    def GetSelectedColor(self, response):
        return response.xpath(
            "//div[contains(@class,'product-sections') and contains(div/text(),'Color')]/span[contains(@class,'selectedColor')]/text()").get()

    def GetPrice(self, response):
        orignalPrice = response.xpath("//div[@id='fullPriceContainer']/span[contains(@id,'retailPrice')]/text()").get()
        if orignalPrice != None:
            return float(str(orignalPrice).replace('$', '').replace(',', ''))
        else:
            regularPrice = response.xpath(
                "//div[@id='salePriceContainer']/s[@id='retailPriceStrikethrough']/text()").get()
            return float(str(regularPrice).replace('$', '').replace(',', ''))

    def GetSalePrice(self, response):
        salePrice = response.xpath(
            "//div[@id='salePriceContainer']/span[contains(@class,'price__sale')]/text()").get()
        if salePrice != None:
            return float(str(salePrice).replace("$", "").replace(',', ''))
        else:
            return 0

    def GetBrand(self, response):
        return str(response.xpath("//a[@property='brand']/span/following-sibling::text()").get()).strip()

    def GetImageUrl(self, response):
        imageUrls = []
        images = response.xpath("//div[@class='slideshow__pager']/a[img[not(@data-swatch)]]/@data-image").extract()
        for image in images:
            imageUrls.append(image)
        return imageUrls

    def GetDescription(self, response):
        return ' '.join(response.xpath("//div[@id='product-details__description']/ul/li/text()").extract()).replace(
            '\n', '').strip()

    def GetSizes(self, response):
        productSizes = []
        colorName = self.GetSelectedColor(response)
        sizeOptions = response.xpath(
            "//div[contains(@class,'product-sizes')]/ul/li/input[not(@disabled)]/following-sibling::label/span[contains(text(),'Size')]/following-sibling::span/text()").extract()
        gender = ProductFilters.objects.get(ProductUrl=GetterSetter.ProductUrl).ParentCategory.split(',')[0]
        for sizeName in sizeOptions:
            fitType = GetFitType(gender, sizeName)
            available = True
            sizelist = str(colorName), str(sizeName), available, str(fitType), 0.0, 0.0
            productSizes.append(sizelist)
        return productSizes

    def GetCategory(self, response):
        siteMapCategory = str(Spider_BaseClass.ProductUrlsAndCategory.get(GetterSetter.ProductUrl)).replace('None', '')
        return siteMapCategory
