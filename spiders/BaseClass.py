import json
import sys
import traceback
import urllib.parse
from pathlib import Path

import requests
import scrapy
from django.db import connection
from django.db.models import Count
from django.db.models import Q
from scrapy.http import HtmlResponse

from WebDriver import SeleniumResponse
from FiltersMapping import *
from SiteSizesDict import *
from SizeMappingList import *
# ========== RETRY ======== #
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

# session = requests.Session()
# retry = Retry(total=5, connect=5, backoff_factor=1)
# adapter = HTTPAdapter(max_retries=retry)
# session.mount('http://', adapter)
# session.mount('https://', adapter)
# ========== END ======== #

cursor = connection.cursor()
onlyScrapperName = str(sys.argv[1]).replace('scrapper', '').replace('scraper', '')
store_url = sys.argv[4]
product_url = urllib.parse.unquote_plus(sys.argv[6])
ScrapeNewUrl = sys.argv[7]
print('ScrapeNewUrl...........>>>', ScrapeNewUrl)
scraper_start_datetime = datetime.datetime.now()
store_id = Store.objects.get(Id=sys.argv[5])


class GetterSetter():
    def __init__(self, ProductUrl):
        self._productUrl = ProductUrl

    @property
    def ProductUrl(self):
        return self._productUrl

    @ProductUrl.setter
    def ProductUrl(self, value):
        self._productUrl = value


# Gender, Body/Fit/Length Type, Regex
FitTypeList = [('Women', 'Petite', r'\b(P(\d+|\w+)|(\d+|\w+)P)\b'),
               ('Women', 'Plus', r'\b((\d+|\w+)X|(\d+|\w+)W)\b'),
               ('Women', 'Tall', r'\b(T(\s?)(\d+|\w+)|(\d+|\w+)(\s?)T)\b'),
               ('Men', 'Short', r'\b((Short|S)((\s|-)?)\d+)|((\d+((\s|-)?)(Short|S)))\b'),
               ('Men', 'Long', r'\b((Long|L)((\s|-)?)\d+)|((\d+((\s|-)?)(Long|L)))\b'),
               ('Men', 'Extra Long', r'\b((Extra((\s|-)?)Long|XL)(\s|-)?\d+)|((\d+(\s|-)?(Extra((\s|-)?)Long|XL)))\b'),
               ('Kids', 'Slim', r'\b((Slim|S)((\s|-)?)\d+)|((\d+((\s|-)?)(Slim|S)))\b'),
               ('Kids', 'Husky', r'\b((Husky)((\s|-)?)\d+)|((\d+((\s|-)?)(Husky)))\b'),
               ('Kids', 'Alpha', r'\b((Alpha)((\s|-)?)\d+)|((\d+((\s|-)?)(Alpha)))\b')]


def GetFitType(gender, size):
    if ('Girl' in gender or 'Boy' in gender) and not 'Baby' in gender:
        gender = 'Kids'

    if 'Baby' in gender or 'infant' in gender:
        return ''
    else:
        fitList = Enumerable(FitTypeList).where(lambda x: x[0] == gender).select(lambda y: y).to_list()
        for fit in fitList:
            if re.search(fit[2], size, re.IGNORECASE):
                return fit[1]
        return 'Regular'


class Spider_BaseClass(scrapy.Spider):
    ScraperErrorList = []
    TotalDistinctProductUrl = []
    AllProductUrl = []
    AllProductUrls = []
    ProductUrlsAndCategory = {}
    cookiesDict = {}
    headersDict = {}
    existingProducts = []
    ProductUpdated = []
    AddCount = 0
    DeletedDBCount = 0
    DeleteWebCount = 0
    MergeCount = 0
    UpdateCount = 0
    WarningCount = 0
    AddCountList = []
    DeletedDBCountList = []
    DeleteWebCountList = []
    MergeCountList = []
    UpdateCountList = []
    WarningCountList = []
    db_urls = []
    out_of_stock = ''
    APIFiltersFlag = True
    errorcountfortesting_removeit = 0
    testingGender = ''
    startUrl = ''
    hasDriver = False

    def parse(self, response):
        for u in Product.objects.filter(StoreId=store_id):
            Spider_BaseClass.db_urls.append(u.Url)
        Spider_BaseClass.db_urls = list(set(Spider_BaseClass.db_urls))

        # Running complete scraper
        if store_url != 'None' and ScrapeNewUrl == 'true':
            print('Scrap new urls...!!!!!!!!!!!')
            if Spider_BaseClass.startUrl != '':
                yield scrapy.Request(Spider_BaseClass.startUrl, cookies=Spider_BaseClass.cookiesDict,
                                     headers=Spider_BaseClass.headersDict, callback=self.GetCategories,
                                     meta={'dont_redirect': True})
            else:
                yield scrapy.Request(response.request.url, cookies=Spider_BaseClass.cookiesDict,
                                     headers=Spider_BaseClass.headersDict, callback=self.GetCategories,
                                     meta={'dont_redirect': True})
        # Testing scrape by url
        elif product_url != 'None':
            GetterSetter.ProductUrl = product_url
            try:
                yield scrapy.Request(response.request.url, cookies=Spider_BaseClass.cookiesDict,
                                     headers=Spider_BaseClass.headersDict, callback=self.GetProducts,
                                     dont_filter=True, meta={'dont_redirect': True})
            except Exception as e:
                self.ExceptionHandlineInGetProductInfo(e, 'GetProductsError',
                                                       'Exception: Exception in GetProducts function.')
        # Running product from database like existing product urls
        elif store_url != 'None' and ScrapeNewUrl == 'false':
            print('Scrap only old urls...!!!!!!!!!!!')
            for existingProductUrl in Spider_BaseClass.db_urls:
                GetterSetter.ProductUrl = existingProductUrl
                try:
                    yield scrapy.Request(existingProductUrl, cookies=Spider_BaseClass.cookiesDict,
                                         headers=Spider_BaseClass.headersDict, callback=self.GetProducts,
                                         dont_filter=True, meta={'dont_redirect': True})
                except Exception as e:
                    self.ExceptionHandlineInGetProductInfo(e, 'GetProductsError',
                                                           'Exception: Exception in GetProducts function.')

    def GetCategories(self, response):
        if Spider_BaseClass.hasDriver:
            seleniumResponse = SeleniumResponse(response.url)
            Spider_BaseClass.AllProductUrl = list(set(self.GetProductUrls(seleniumResponse)))
        else:
            Spider_BaseClass.AllProductUrl = list(set(self.GetProductUrls(response)))

        print('DB Urls', len(Spider_BaseClass.db_urls))
        print('Web Urls', len(Spider_BaseClass.AllProductUrl))
        print('DB & Web Urls', len(Spider_BaseClass.AllProductUrl) + len(Spider_BaseClass.db_urls))

        Spider_BaseClass.TotalDistinctProductUrl = list(set(Spider_BaseClass.AllProductUrl + Spider_BaseClass.db_urls))
        print('Distinct Urls', len(Spider_BaseClass.TotalDistinctProductUrl))

        Product.objects.filter(StoreId=store_id).update(UpdatedOrAddedOnLastRun=0)

        for productUrl in Spider_BaseClass.TotalDistinctProductUrl:
            try:
                GetterSetter.ProductUrl = productUrl
                productres = requests.get(productUrl, cookies=Spider_BaseClass.cookiesDict,
                                          headers=Spider_BaseClass.headersDict)
                productResponse = HtmlResponse(url=productUrl, body=productres.text, encoding='utf-8')
                self.GetProducts(productResponse)
            except Exception as e:
                self.ExceptionHandlineInGetProductInfo(e, 'GetProductsError',
                                                       'Exception: Exception in GetProducts function.')
                continue

    def GetProducts(self, response):
        if Spider_BaseClass.hasDriver:
            response = SeleniumResponse(response.url)

        try:
            ignorProduct = self.IgnoreProduct(response)
            if ignorProduct:
                self.ProductIsOutofStock(GetterSetter.ProductUrl)
            else:
                self.GetProductInfo(response)
        except Exception as e:
            self.ExceptionHandlineInGetProductInfo(e, 'GetProductsError',
                                                   'Exception: Exception in GetProducts function.')
            return

    def ProductIsOutofStock(self, out_of_stock_url):
        if store_url != 'None':
            if Product.objects.filter(Url=out_of_stock_url.replace('https://', '').replace('http://',
                                                                                           '')).exists():
                Spider_BaseClass.DeletedDBCountList.append(out_of_stock_url)
                Spider_BaseClass.DeletedDBCount += 1
            else:
                Spider_BaseClass.DeleteWebCountList.append(out_of_stock_url)
                Spider_BaseClass.DeleteWebCount += 1
        else:
            Spider_BaseClass.out_of_stock = 'Out of stock.'
            self.SaveScrapByUrlJsonFile()

    def GetProductInfo(self, response):
        name = ''
        image = ''
        description = ''
        brand = ''
        category = ''
        sale_price = 0.0
        orignal_price = 0.0
        url = response.url
        try:
            url = GetterSetter.ProductUrl
            if not url:
                raise NotImplementedError("No url found, Raising No url exception")
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno)
            tb = traceback.format_exception(etype=type(e), value=e, tb=e.__traceback__)
            error = ['Url Error', 'Error while fetching URL.', exc_type, fname, exc_tb.tb_lineno, [url], tb]
            self.ScrperError(error)
            return

        try:
            name = self.GetName(response)
            if not name:
                raise NotImplementedError("No product name found ,Raising No name exception")
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno)
            tb = traceback.format_exception(etype=type(e), value=e, tb=e.__traceback__)
            error = ['Name Error', 'Error while fetching Name.', exc_type, fname, exc_tb.tb_lineno, [url], tb]
            self.ScrperError(error)
            return
        try:
            orignal_price = round(float(self.GetPrice(response)), 2)
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno)
            tb = traceback.format_exception(etype=type(e), value=e, tb=e.__traceback__)
            error = ['Original Price Error', 'Error while fetching Original Price.', exc_type, fname, exc_tb.tb_lineno,
                     [url], tb]
            self.ScrperError(error)
            return
        try:
            sale_price = round(float(self.GetSalePrice(response)), 2)
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno)
            tb = traceback.format_exception(etype=type(e), value=e, tb=e.__traceback__)
            error = ['Sale Price Error', 'Error while fetching Sale Price.', exc_type, fname, exc_tb.tb_lineno, [url],
                     tb]
            self.ScrperError(error)
            return
        try:
            if orignal_price == sale_price:
                sale_price = 0.0
            elif sale_price > orignal_price:
                raise NotImplementedError("Exception: Sale price is higher tha regular price.")
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno)
            tb = traceback.format_exception(etype=type(e), value=e, tb=e.__traceback__)
            error = ['Sale Price Higher Error', 'Exception: Sale price is higher tha regular price.', exc_type, fname,
                     exc_tb.tb_lineno, [url], tb]
            self.ScrperError(error)
            return
        try:
            brand = self.GetBrand(response)
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno)
            tb = traceback.format_exception(etype=type(e), value=e, tb=e.__traceback__)
            error = ['Brand Error', 'Error while fetching Brand.', exc_type, fname, exc_tb.tb_lineno, [url], tb]
            self.ScrperError(error)
            return
        try:
            description = re.sub(r'(<!--.*?-->|<[^>]*>)|\s+', " ", str(self.GetDescription(response))).strip(' ')
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno)
            tb = traceback.format_exception(etype=type(e), value=e, tb=e.__traceback__)
            error = ['Description Error', 'Error while fetching Description.', exc_type, fname, exc_tb.tb_lineno, [url],
                     tb]
            self.ScrperError(error)
            return
        try:
            category = self.GetCategory(response)
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno)
            tb = traceback.format_exception(etype=type(e), value=e, tb=e.__traceback__)
            error = ['Category Error', 'Error while fetching Category.', exc_type, fname, exc_tb.tb_lineno, [url],
                     tb]
            self.ScrperError(error)
            return
        try:
            APIFilters(url, name, category, description)
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno)
            tb = traceback.format_exception(etype=type(e), value=e, tb=e.__traceback__)
            error = ['Filters Error', 'Error while fetching API Filters.', exc_type, fname, exc_tb.tb_lineno, [url], tb]
            self.ScrperError(error)
            return
        try:
            image = self.GetImageUrl(response)
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno)
            tb = traceback.format_exception(etype=type(e), value=e, tb=e.__traceback__)
            error = ['Image Error', 'Error while fetching Images URL.', exc_type, fname, exc_tb.tb_lineno, [url], tb]
            self.ScrperError(error)
            return
        try:
            pro_Sizes = self.GetSizes(response)
            sizesAvbls = list(set(Enumerable(pro_Sizes).select(lambda x: x[2]).to_list()))
            if len(sizesAvbls) == 1 and sizesAvbls[0] == 'False':
                self.ProductIsOutofStock(url)
                print('Skipped Product: All product sizes are unavailable')
                return
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno)
            tb = traceback.format_exception(etype=type(e), value=e, tb=e.__traceback__)
            error = ['Size Error', 'Error while fetching Sizes.', exc_type, fname, exc_tb.tb_lineno, [url], tb]
            self.ScrperError(error)
            return
        pro = [name, url, orignal_price, sale_price, category, brand, description,
               image, pro_Sizes]
        self.ScrapeResultDeatils(pro)

    def ExceptionHandlineInGetProductInfo(self, e, msg, detail):
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        tb = traceback.format_exception(etype=type(e), value=e, tb=e.__traceback__)
        print(exc_type, fname, exc_tb.tb_lineno)
        print(tb)
        error = [msg, detail, exc_type, fname,
                 exc_tb.tb_lineno, [GetterSetter.ProductUrl], tb]
        self.ScrperError(error)
        return

    def index_2d(self, myList, v):
        for i, x in enumerate(myList):
            if v in x:
                return [i, x.index(v)]
        return False

    def SaveScrapByUrlJsonFile(self):

        if Spider_BaseClass.ScraperErrorList:
            data = {
                'Error_in': Spider_BaseClass.ScraperErrorList[0][0],
                'Error_msg': Spider_BaseClass.ScraperErrorList[0][1],
                'Error_class': str(Spider_BaseClass.ScraperErrorList[0][2]),
                'Error_taceback': (Spider_BaseClass.ScraperErrorList[0][6]),
                'Error_url': product_url,
                'Error_Flag': 'True',
                'out_of_stock': Spider_BaseClass.out_of_stock
            }
        elif Spider_BaseClass.out_of_stock:
            data = {
                'Error_in': '',
                'Error_msg': '',
                'Error_class': '',
                'Error_taceback': '',
                'Error_url': product_url,
                'Error_Flag': 'Out of stock.',
                'out_of_stock': Spider_BaseClass.out_of_stock
            }
        else:
            data = {
                'Results': Spider_BaseClass.ProductUpdated[0],
                'Error_Flag': "False",
                'out_of_stock': Spider_BaseClass.out_of_stock
            }
        try:
            with open(str(Path(__file__).resolve().parent) + '\\' + 'ProductFileTemp.json', 'w',
                      encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            print('ProductFileTemp.json file saved.')
        except Exception as e:
            print(e)

    def DeleteDBRecord(self, url):
        if Product.objects.filter(Url=url, StoreId=store_id).exists():
            ProductId = Product.objects.filter(Url=url, StoreId=store_id)[0].Id
            ProductSize.objects.filter(ProductId=ProductId).delete()
            Product.objects.filter(Id=ProductId).delete()

    def SaveProductsAndSizeInDb(self):
        mappedDict = {}
        try:
            matchedSizes = []
            sizesAndFitType = []

            menCatList = ['Shirt', 'Pant', 'Suit','Jeans', 'Dress']
            genderList = ['Women', 'Men', 'Baby', 'Girl', 'Boy']
            menCatDict = {'Shirt': r"\b((Shirt)(-|')?(s?))\b", 'Pant': r"\b((Trouser|Pant)(-|')?(s?))\b",
                          'Suit': r"\b((Jacket|Waistcoat|Coat|Suit)(-|')?(s?))\b", "Jeans": r'Jeans', 'Dress': r'Dress'}
            genderDict = {'Women': r"\b((Women|Woman)(-|')?(s?))\b", 'Men': r"\b((Men|Man)(-|')?(s?))\b",
                          'Girl': r"\b((Girl)(-|')?(s?))\b", 'Boy': r"\b((Boy)(-|')?(s?))\b",
                          'Baby': r"\b(Infant|(Baby|New((\s|-)?)Born(\s|-)(Boy|Girl)(-|')?(s?)))\b"}

            for gender in genderList:
                if gender == 'Girl' or gender == 'Boy':
                    genderSizes = Enumerable(Spider_BaseClass.ProductUpdated).where(
                        lambda x: re.search(genderDict[gender], x[4], re.IGNORECASE) and not re.search(
                            genderDict['Baby'], x[4], re.IGNORECASE) and not re.search(
                            genderDict['Women'], x[4], re.IGNORECASE)).select(
                        lambda x: (x[4], x[8])).to_list()
                else:
                    genderSizes = Enumerable(Spider_BaseClass.ProductUpdated).where(
                        lambda x: re.search(genderDict[gender], x[4], re.IGNORECASE)).select(
                        lambda x: (x[0]+" "+x[4], x[8])).to_list()

                # if genderSizes and gender != 'Men':
                #     sizesAndFitType = list(
                #         set(sizesAndFitType + list(set(Enumerable(genderSizes).select_many(lambda x: x[1]).select(
                #             lambda x: (x[3], x[1], gender, '')).to_list()))))
                # else:
                print("genderSize : ", genderSizes)
                for genderSize in genderSizes:
                    for menCat in menCatList:
                        if re.search(menCatDict[menCat], genderSize[0], re.IGNORECASE):
                            sizesAndFitType = list(set(sizesAndFitType + list(set(Enumerable(genderSize[1]).select(
                                lambda x: (x[3], x[1], gender, menCat)).to_list()))))


            print('Unique Sizes: ', sizesAndFitType)
            print('Unique Sizes Length: ', len(sizesAndFitType))

            for sizeAndFitType in sizesAndFitType:
                sizeNameOrg = sizeAndFitType[1]
                sizeName = ''
                print("---------------->>>>sizeName", sizeNameOrg)
                mapList, siteMapDict = self.GetSizeMapList(sizeAndFitType[2], sizeAndFitType[3])
                if siteMapDict and siteMapDict.get(sizeNameOrg) is not None:
                    sizeName = siteMapDict[sizeNameOrg]
                print("---------------->>>>sizeNameif", sizeName)

                if sizeAndFitType[2] == 'Baby':
                    fitList = mapList
                else:
                    fitList = Enumerable(mapList).where(lambda x: x[0] == sizeAndFitType[0]).select(
                        lambda y: y).to_list()

                for fit in fitList:
                    if fit[3] != '' and re.search(fit[3], sizeName, re.IGNORECASE):
                        if fit[5] != '' and re.search(fit[5], sizeName, re.IGNORECASE):
                            sizeName = re.sub(fit[5], '', sizeName, re.IGNORECASE).strip()

                        # else:
                        #     refinedSize = sizeName
                        # print(refinedSize)


                        if fit[3] != '' and re.search(fit[3], sizeName, re.IGNORECASE):
                            mappedDict[sizeAndFitType[0] + " " + sizeNameOrg + " " + sizeAndFitType[3]] = fit[1]
                            # list(sizeAndFitType)[1] = sizeAndFitType[1]
                            print("sizeAndFitType : ", sizeAndFitType)
                            print(mappedDict)
                            matchedSizes.append(tuple(list(sizeAndFitType)))
                            break


                            # mappedDict[sizeAndFitType[0] + " " + refinedSize + " " + sizeAndFitType[3]] = fit[1]
                            # list(sizeAndFitType)[1] = refinedSize
                            # sizeAndFitType = sizeAndFitType[0],refinedSize,sizeAndFitType[2],sizeAndFitType[3]
                            # print(sizeAndFitType)
                            # matchedSizes.append(tuple(list(sizeAndFitType)))


            unMatchedSizes = list(set(sizesAndFitType) - set(matchedSizes))
            if unMatchedSizes:
                print('UnMapped Sizes After Character Regex: ', unMatchedSizes)
                print('Character UnMapped Sizes Length: ', len(unMatchedSizes))

                for sizeAndFitType in unMatchedSizes:
                    mapList, siteMapDict = self.GetSizeMapList(sizeAndFitType[2], sizeAndFitType[3])
                    fitList = Enumerable(mapList).where(lambda x: x[0] == sizeAndFitType[0]).select(
                        lambda y: y).to_list()

                    sizeName = sizeAndFitType[1]
                    if siteMapDict and siteMapDict.get(sizeName) is not None:
                        sizeName = siteMapDict[sizeName]

                    for fit in fitList:
                        if fit[4] != '' and re.search(fit[4], sizeName, re.IGNORECASE):
                            mappedDict[sizeAndFitType[0] + " " + sizeName + " " + sizeAndFitType[3]] = fit[1]
                            list(sizeAndFitType)[1] = sizeAndFitType[1]
                            matchedSizes.append(tuple(list(sizeAndFitType)))

                unMatchedSizes = list(set(sizesAndFitType) - set(matchedSizes))
                if unMatchedSizes:
                    print('UnMapped Sizes After Integer Regex: ', unMatchedSizes)
                    print('Integer UnMapped Sizes Length: ', len(unMatchedSizes))

            print('Mapped Sizes: ', mappedDict)
            print('Mapped Sizes Length: ', len(mappedDict))
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno)
            tb = traceback.format_exception(etype=type(e), value=e, tb=e.__traceback__)
            error = ['Size Mapping Error', 'Error while Mapping Sizes.', exc_type, fname, exc_tb.tb_lineno, [None],
                     tb]
            self.ScrperError(error)
            pass

        print("Delete Count: ", Spider_BaseClass.DeletedDBCount)
        print("Delete List: ", Spider_BaseClass.DeletedDBCountList)
        print("Merged Count: ", Spider_BaseClass.MergeCount)
        print("Merged List: ", Spider_BaseClass.MergeCountList)
        print("Warn Count: ", Spider_BaseClass.WarningCount)
        print("Warn List: ", Spider_BaseClass.WarningCountList)
        print('Saving Products And Sizes In Db => Product Added/Updated Length: ',
              len(Spider_BaseClass.ProductUpdated))

        for n in Spider_BaseClass.ProductUpdated:
            try:
                if Product.objects.filter(Name=n[0], Url=n[1], StoreId=store_id).exists():
                    Product.objects.filter(Url=n[1], StoreId=store_id, Name=n[0]).update(UpdatedOrAddedOnLastRun=1,
                                                                                         Description=n[6],
                                                                                         ImageUrl=n[7],
                                                                                         Price=n[2], SalePrice=n[3],
                                                                                         Brand=n[5], Category=n[4],
                                                                                         DateUpdated=datetime.datetime.now())

                    productId = Product.objects.filter(Url=n[1], StoreId=store_id, Name=n[0])[0]
                    print("n[8] : ", n[8])
                    hasSaved = self.SaveProductSizes(n[8], productId, n[1], mappedDict, n[0] + " " + n[4])
                    if hasSaved == True:
                        Spider_BaseClass.UpdateCount += 1
                        Spider_BaseClass.UpdateCountList.append(n)
                    else:
                        continue
                elif Product.objects.filter((~Q(Name=n[0])), Url=n[1], StoreId=store_id).exists():
                    ProductId = Product.objects.filter((~Q(Name=n[0])), Url=n[1], StoreId=store_id)[0].Id
                    ProductSize.objects.filter(ProductId=ProductId).delete()
                    Product.objects.filter(Id=ProductId).delete()

                    Product(UpdatedOrAddedOnLastRun=1, Url=n[1], StoreId=store_id, Name=n[0], Description=n[6],
                            ImageUrl=n[7], Price=n[2],
                            SalePrice=n[3], Brand=n[5],
                            Category=n[4]).save()
                    print("n[8] : ", n[8])

                    hasSaved = self.SaveProductSizes(n[8], Product.objects.latest('Id'), n[1], mappedDict,
                                                     n[0] + " " + n[4])
                    if hasSaved == True:
                        Spider_BaseClass.AddCount += 1
                        Spider_BaseClass.AddCountList.append(n)
                    else:
                        continue
                else:
                    Product(UpdatedOrAddedOnLastRun=1, Url=n[1], StoreId=store_id, Name=n[0], Description=n[6],
                            ImageUrl=n[7], Price=n[2],
                            SalePrice=n[3], Brand=n[5],
                            Category=n[4]).save()
                    print("n[8] : ", n[8])
                    hasSaved = self.SaveProductSizes(n[8], Product.objects.latest('Id'), n[1], mappedDict,
                                                     n[0] + " " + n[4])
                    if hasSaved == True:
                        Spider_BaseClass.AddCount += 1
                        Spider_BaseClass.AddCountList.append(n)
                    else:
                        continue
            except Exception as e:
                exc_type, exc_obj, exc_tb = sys.exc_info()
                fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                print(exc_type, fname, exc_tb.tb_lineno)
                tb = traceback.format_exception(etype=type(e), value=e, tb=e.__traceback__)
                error = ['Product Saving Error', 'Error while Saving Product Data in DB', exc_type, fname,
                         exc_tb.tb_lineno, [n[1]],
                         tb]
                self.ScrperError(error)
            continue
        print('Saved Products And Size In Db => Product Added/Updated Length: ',
              Spider_BaseClass.AddCount + Spider_BaseClass.UpdateCount)
        return

    def GetSizeMapList(self, gender, type):
        try:
            if type:
                if siteSizesDict.get(onlyScrapperName + gender + type + "_Dict") is not None:
                    mapListAndDict = sizeMappingList[gender.lower() + type + 'MapList'], siteSizesDict[
                        onlyScrapperName + gender + type + "_Dict"]
                else:
                    mapListAndDict = sizeMappingList[gender.lower() + type + 'MapList'], {}
                return mapListAndDict
            else:
                if siteSizesDict.get(onlyScrapperName + gender + "_Dict") is not None:
                    mapListAndDict = sizeMappingList[gender.lower() + 'MapList'], siteSizesDict[
                        onlyScrapperName + gender.title() + "_Dict"]
                else:
                    mapListAndDict = sizeMappingList[gender.lower() + 'MapList'], {}

                if gender == 'Girl' or gender == 'Boy':
                    inclToddler = list(mapListAndDict)
                    inclToddler[0] = sizeMappingList['toddlerMapList'] + inclToddler[0]
                    return inclToddler
                else:
                    return mapListAndDict
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno)
            tb = traceback.format_exception(etype=type(e), value=e, tb=e.__traceback__)
            error = ['Size Mapping List/Dict Error', 'Error while Getting Sizes Mapping List/Dict.', exc_type, fname,
                     exc_tb.tb_lineno, [None],
                     tb]
            self.ScrperError(error)
            pass

        return [], {}

    def SaveProductSizes(self, sizeObjects, productId, productUrl, mappedDict, category):
        try:
            categoryType = ''
            print("sizeObjects ",sizeObjects)
            gender = ProductFilters.objects.get(ProductUrl=productUrl).ParentCategory.split(',')[0]
            menCatList = ['Shirt', 'Pant', 'Suit', 'Jeans', 'Dress']
            menCatDict = {'Shirt': r"\b((Shirt)(-|')?(s?))\b", 'Pant': r"\b((Trouser|Pant)(-|')?(s?))\b",
                          'Suit': r"\b((Jacket|Waistcoat|Coat|Suit)(-|')?(s?))\b","Jeans": r'Jeans', 'Dress': r'Dress'}
            # if gender == 'Men':
            for menCat in menCatList:
                if re.search(menCatDict[menCat], category, re.IGNORECASE):
                    categoryType = menCat
                    break
            else:
                categoryType = ''
            for sizeObject in sizeObjects:
                szc = 1 if sizeObject[2] else 0
                mappedSize = str(mappedDict.get(sizeObject[3] + " " + sizeObject[1] + " " + categoryType)).replace(
                    'None', '')
                if ProductSize.objects.filter(ProductId=productId, Size=sizeObject[1], Color=sizeObject[0],
                                              FitType=sizeObject[3]).exists():
                    print("---------------------------------------->>>>>>>>>>>>>>>>>>save")
                    print(mappedSize)
                    ProductSize.objects.filter(
                        ProductId=productId, Size=sizeObject[1], Color=sizeObject[0], FitType=sizeObject[3]).update(
                        Size=sizeObject[1], Color=sizeObject[0], Available=szc, FitType=sizeObject[3],
                        Price=sizeObject[4], SalePrice=sizeObject[5], MappedSize=mappedSize)
                else:
                    print("---------------------------------------->>>>>>>>>>>>>>>>>>prod")
                    ProductSize(ProductId=productId, Size=sizeObject[1], Color=sizeObject[0],
                                Available=szc, FitType=sizeObject[3], Price=sizeObject[4],
                                SalePrice=sizeObject[5], MappedSize=mappedSize).save()

        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno)
            tb = traceback.format_exception(etype=type(e), value=e, tb=e.__traceback__)
            error = ['Size Saving Error', 'Error while Saving Sizes Data in DB', exc_type, fname, exc_tb.tb_lineno,
                     [productUrl],
                     tb]
            self.ScrperError(error)
            return False
        return True

    def spider_closed(self, spider):
        try:
            if store_url != 'None':
                print('New ProductUrl Count: ', len(Spider_BaseClass.AllProductUrl))
                ExistingProductUrlCount = len(Spider_BaseClass.db_urls)
                self.SaveProductsAndSizeInDb()  # Function for saving products in db with sizes and colours
                print('Total Distinct ProductUrl Count: ', len(Spider_BaseClass.TotalDistinctProductUrl))
                # find sizes and brand for only those updated_templist
                TotalProductSizeCount = ProductSize.objects.filter(ProductId__StoreId=store_id, ProductId__Deleted=0,
                                                                   ProductId__UpdatedOrAddedOnLastRun=1).count()
                ProductWithProductSizeCount = (
                    ProductSize.objects.filter(ProductId__StoreId=store_id, ProductId__Deleted=0,
                                               ProductId__UpdatedOrAddedOnLastRun=1).values(
                        'ProductId').annotate(ProductId_count=Count('pk')).order_by('ProductId'))
                ProductSizeAvailableCount = ProductSize.objects.filter(ProductId__StoreId=store_id, Available=1,
                                                                       ProductId__Deleted=0,
                                                                       ProductId__UpdatedOrAddedOnLastRun=1).count()
                ProductWithBrandCount = Product.objects.filter(StoreId=store_id,
                                                               UpdatedOrAddedOnLastRun=1).exclude(Q(Brand='')).count()
                UniqueBrandCount = Product.objects.filter(StoreId=store_id, UpdatedOrAddedOnLastRun=1).exclude(
                    Q(Brand='')).values('Brand').distinct()
                ScrapErrorDistinctList = []
                for i, row in enumerate(Spider_BaseClass.ScraperErrorList):
                    result = self.index_2d(ScrapErrorDistinctList, row[1])
                    print(result)
                    ScrapErrorDistinctList.append(row) if result == False else ScrapErrorDistinctList[result[0]][
                        5].append(
                        row[5][0])
                    if not ScrapErrorDistinctList:
                        ScrapErrorDistinctList.append(row)
                ErrorCount = 0
                for errors in ScrapErrorDistinctList:
                    ErrorCount += len(errors[5])
                # ______________________________________________________________________________________________________
                ProductSizeWithColorCountDict = (
                    ProductSize.objects.filter(ProductId__StoreId=store_id, ProductId__Deleted=0,
                                               ProductId__UpdatedOrAddedOnLastRun=1).exclude(Q(Color='')).values(
                        'ProductId').annotate(
                        color_count=Count('pk'))
                ).order_by('Color')
                ProductSizeWithColorCount = 0
                for r in ProductSizeWithColorCountDict:
                    ProductSizeWithColorCount += r['color_count']
                # ______________________________________________________________________________________________________

                if ScrapeNewUrl == 'false':
                    Spider_BaseClass.AllProductUrl = 0
                ScrapResult(StoreId=store_id, ScrapTypeId=ScrapType.objects.filter(StoreId=store_id)[0],
                            StartDateTime=scraper_start_datetime, EndDateTime=datetime.datetime.now(),
                            NewProductUrlCount=len(Spider_BaseClass.AllProductUrl),
                            ExistingProductUrlCount=ExistingProductUrlCount,
                            TotalDistinctProductUrlCount=len(Spider_BaseClass.TotalDistinctProductUrl),
                            ProductAddedCount=Spider_BaseClass.AddCount,
                            ProductUpdatedCount=Spider_BaseClass.UpdateCount,
                            ProductDeletedCount=len(Spider_BaseClass.DeletedDBCountList),
                            ProductMergedCount=Spider_BaseClass.MergeCount, SaleProductCount=len(
                        Enumerable(Spider_BaseClass.ProductUpdated).where(lambda x: float(x[3]) != 0.0).to_list()),
                            TotalProductCount=(Spider_BaseClass.AddCount + Spider_BaseClass.UpdateCount),
                            DownloadThreadCount=0,
                            WarningCount=Spider_BaseClass.WarningCount,
                            ErrorCount=ErrorCount, DateCreated=datetime.datetime.now(),
                            ProductWithProductSizeCount=len(ProductWithProductSizeCount),
                            ProductSizeAvailableCount=ProductSizeAvailableCount,
                            ProductSizeWithColorCount=ProductSizeWithColorCount,
                            TotalProductSizeCount=TotalProductSizeCount, ScrapThreadCount=0,
                            ProductWithBrandCount=ProductWithBrandCount, UniqueBrandCount=len(UniqueBrandCount)
                            ).save()

                for errors in ScrapErrorDistinctList:
                    StackTrace = json.dumps(errors[6])
                    ScrapError(ScrapResultId=ScrapResult.objects.filter(StoreId=store_id).latest('Id'),
                               Message=errors[1],
                               StackTrace=StackTrace, UrlList=json.dumps(errors[5]), Count=len(errors[5]),
                               Exception=errors[2],
                               DateCreated=datetime.datetime.now()).save()
                if Spider_BaseClass.WarningCountList or Spider_BaseClass.MergeCountList or Spider_BaseClass.DeletedDBCountList:
                    DeletedList = Spider_BaseClass.DeletedDBCountList if Spider_BaseClass.DeletedDBCountList else None
                    DeletedWebList = Spider_BaseClass.DeleteWebCountList if Spider_BaseClass.DeleteWebCountList else None
                    WarningList = Spider_BaseClass.WarningCountList if Spider_BaseClass.WarningCountList else None
                    MergeList = Spider_BaseClass.MergeCountList if Spider_BaseClass.MergeCountList else None
                    ProductMergedAndWarning(ScrapResultId=ScrapResult.objects.filter(StoreId=store_id).latest('Id'),
                                            MergedList=str(MergeList), DeletedDBList=str(DeletedList),
                                            DeletedWebList=str(DeletedWebList),
                                            WarningList=str(WarningList)).save()
                print('Spider closed: %s', spider.name)
            else:
                self.SaveScrapByUrlJsonFile()
                print('Spider ' + spider.name + ' for Product url ' + product_url + ' is completed.')
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno)
            tb = traceback.format_exception(etype=type(e), value=e, tb=e.__traceback__)
            error = ['Scrap Result Saving Error', 'Error while Saving Scrap result', exc_type, fname, exc_tb.tb_lineno,
                     [],
                     tb]
            self.ScrperError(error)
            return False

    def ScrperError(self, nameErr):
        print(nameErr)
        Spider_BaseClass.ScraperErrorList.append(nameErr)
        return

    def ScrapeResultDeatils(self, productDetail):
        name, url, orignal_price, sale_price, category, brand, description, image, pro_Sizes = \
            productDetail[0], productDetail[1], productDetail[2], productDetail[3], productDetail[4], productDetail[5], \
            productDetail[6], productDetail[7], productDetail[8]
        if store_url != 'None':
            if not Spider_BaseClass.existingProducts:
                Spider_BaseClass.existingProducts = list(
                    Product.objects.filter(StoreId=store_id).values_list('Name', 'Url', 'Price', 'SalePrice'))

            product = [name, url, orignal_price, sale_price, category, brand, description,
                       image, pro_Sizes]
            url = self.search_id_2dlist(product, Spider_BaseClass.existingProducts)
            if url == True:
                pass
            else:
                Spider_BaseClass.ProductUpdated.append(
                    [name, url, orignal_price, sale_price, category, brand, description,
                     image, pro_Sizes])
                Spider_BaseClass.existingProducts.append([name, url, orignal_price, sale_price])
        else:
            if len(description) > 200:
                description_truncate = description[:200] + '.....'
            else:
                description_truncate = description
            Spider_BaseClass.ProductUpdated.append(
                [name, url, orignal_price, sale_price, category, brand, description_truncate,
                 image, pro_Sizes])

    def search_id_2dlist(self, pro, exPro):
        i = 0
        for exProObj in exPro:
            if pro[0] == exProObj[0] and pro[1] == exProObj[1]:
                return exProObj[1]
            if pro[0] == exProObj[0] and pro[1] != exProObj[1]:
                redUrl = self.GetRedirectedUrl(exProObj[1])
                if pro[1] == redUrl:
                    print('Redirected Url: ', redUrl)
                    return redUrl
                elif float(pro[3]) == float(exProObj[3]):
                    if float(pro[2]) == float(exProObj[2]):
                        print('Product to be Merged: Same Price')
                        Spider_BaseClass.MergeCount += 1
                        Spider_BaseClass.MergeCountList.append(pro[1])
                        return True
                    else:
                        print('Product to be Merged: Different Price')
                        Spider_BaseClass.WarningCount += 1
                        Spider_BaseClass.WarningCountList.append(pro[1])
                        return True
                else:
                    print('Product to be Merged: Different Price')
                    Spider_BaseClass.WarningCount += 1
                    Spider_BaseClass.WarningCountList.append(pro[1])
                    return True
            elif pro[0] != exProObj[0] and pro[1] == exProObj[1]:
                print('Deleting Product')
                self.DeleteDBRecord(exProObj[1])
                Spider_BaseClass.DeletedDBCount += 1
                Spider_BaseClass.DeletedDBCountList.append(exProObj[1])
                del exPro[i]
                print('Adding New Product')
                Spider_BaseClass.UpdateCountList.append(pro)
                exPro.append([pro[0], pro[1], pro[2], pro[3]])
                pro[1] = self.search_id_2dlist(pro, exPro)
                return pro[1]
            i += 1
        return pro[1]

    def GetRedirectedUrl(self, myurl):
        response = requests.get(myurl, cookies=Spider_BaseClass.cookiesDict, headers=Spider_BaseClass.headersDict)
        if response.history:
            for resp in response.history:
                print(resp.status_code, resp.url)
            print(response.status_code, response.url)
            return response.url
        else:
            return myurl

    def GetProductUrls(self, response):
        pass

    def IgnoreProduct(self, response):
        return False

    def GetName(self, response):
        pass

    def GetUPC_SKU(self, response):
        pass

    def GetPrice(self, response):
        pass

    def GetSalePrice(self, response):
        pass

    def GetCategory(self, response):
        pass

    def GetBrand(self, response):
        pass

    def GetDescription(self, response):
        pass

    def GetImageUrl(self, response):
        pass

    def GetSizes(self, response):
        pass
