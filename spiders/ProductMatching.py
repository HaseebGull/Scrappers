import django
import os
import sys
from datetime import datetime

try:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "FashionStores.settings")
    django.setup()
except:
    sys.path.append("E:\\JOB\\Github\\GithubAfterFilter\\")
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "FashionStores.settings")
    django.setup()
from FashionStores.models import Product, ProductSize, ProductFilters, MatchedProduct, SimilarProduct
from django.db.models import Q
from functools import reduce


class ProductMatchingClass:
    def __init__(self):
        try:
            self.group_id = MatchedProduct.objects.latest('Id').GroupId + 1
        except Exception as e:
            self.group_id = 1
        try:
            self.similar_group_id = SimilarProduct.objects.latest('Id').GroupId + 1
        except Exception as e:
            self.similar_group_id = 1

    def ProductMatchingRatio(self, productNameforMatching, ProductName):
        print('productNameforMatching', productNameforMatching)
        print('ProductName', ProductName)
        samecount, product_matching_ratio = 0, 0
        str1words = str(ProductName).split(' ')
        totalcount = len(str1words)
        for word in str1words:
            if word.lower() in str(productNameforMatching).lower():
                samecount += 1
        product_matching_ratio = samecount / totalcount
        return product_matching_ratio

    def FindFilter(self, ProductFiltersMain, Filters_List, ProductId, groupId):
        filter_Numbers = [ProductId, groupId]
        filter_Numbers.append(0) if ProductFiltersMain.Character == 'Not Specified' else filter_Numbers.append(1)
        filter_Numbers.append(0) if ProductFiltersMain.Closure == 'Not Specified' else filter_Numbers.append(1)
        filter_Numbers.append(0) if ProductFiltersMain.DressLength == 'Not Specified' else filter_Numbers.append(1)
        filter_Numbers.append(0) if ProductFiltersMain.DressStyle == 'Not Specified' else filter_Numbers.append(1)
        filter_Numbers.append(0) if ProductFiltersMain.Embellishment == 'Not Specified' else filter_Numbers.append(1)
        filter_Numbers.append(0) if ProductFiltersMain.Feature == 'Not Specified' else filter_Numbers.append(1)
        filter_Numbers.append(0) if ProductFiltersMain.FitType == 'Not Specified' else filter_Numbers.append(1)
        filter_Numbers.append(0) if ProductFiltersMain.GarmentCare == 'Not Specified' else filter_Numbers.append(1)
        filter_Numbers.append(0) if ProductFiltersMain.Material == 'Not Specified' else filter_Numbers.append(1)
        filter_Numbers.append(0) if ProductFiltersMain.Neckline == 'Not Specified' else filter_Numbers.append(1)
        filter_Numbers.append(0) if ProductFiltersMain.Occasion == 'Not Specified' else filter_Numbers.append(1)
        filter_Numbers.append(0) if ProductFiltersMain.Pattern == 'Not Specified' else filter_Numbers.append(1)
        filter_Numbers.append(0) if ProductFiltersMain.FasteningType == 'Not Specified' else filter_Numbers.append(1)
        filter_Numbers.append(0) if ProductFiltersMain.CuffStyle == 'Not Specified' else filter_Numbers.append(1)
        filter_Numbers.append(0) if ProductFiltersMain.Collar == 'Not Specified' else filter_Numbers.append(1)
        filter_Numbers.append(0) if ProductFiltersMain.SleveesLength == 'Not Specified' else filter_Numbers.append(1)
        filter_Numbers.append(0) if ProductFiltersMain.SleveesType == 'Not Specified' else filter_Numbers.append(1)
        filter_Numbers.append(0) if ProductFiltersMain.Themes == 'Not Specified' else filter_Numbers.append(1)
        filter_Numbers.append(0) if ProductFiltersMain.Season == 'Not Specified' else filter_Numbers.append(1)
        filter_Numbers.append(0) if ProductFiltersMain.ShowOnly == 'Not Specified' else filter_Numbers.append(1)
        filter_Numbers.append(0) if ProductFiltersMain.ShowOnly == 'Not Specified' else filter_Numbers.append(1)
        Filters_List.append(filter_Numbers)
        return Filters_List

    def SearchSameProductInDb(self, productIdMain, productNameMain, productNamefMain_w_o_color, Brand_Main,
                              productUrlMain, StoreId, search_type):
        product_matched_data = []
        # filter(~Q(Id=productIdMain,StoreId=StoreId)) [~Q(StoreId=StoreId)) will work for both not same store and same product for which we are searching]
        all_products = []
        print('Search type :', search_type, ' for main id:', productIdMain)
        if search_type == 'Comparison':
            groupId = self.group_id
            all_products = Product.objects.filter(reduce(lambda x, y: x | y, [
                Q((~Q(StoreId=StoreId)), Name__contains=word, Brand=Brand_Main) for word in
                productNamefMain_w_o_color.split(' ')]))
        else:
            groupId = self.similar_group_id
            all_products = Product.objects.filter(reduce(lambda x, y: x | y,
                                                         [Q((~Q(Id=productIdMain)), Name__contains=word) for word in
                                                          productNamefMain_w_o_color.split(' ')]))
        ProductFiltersMain = ProductFilters.objects.filter(ProductUrl=productUrlMain)[0]
        Filters_List = []
        Filters_List = self.FindFilter(ProductFiltersMain, Filters_List, productIdMain, groupId)
        for product in all_products:
            product_matching_ratio = self.ProductMatchingRatio(productNamefMain_w_o_color, product.Name)
            print('product_matching_ratio is', product_matching_ratio)
            if product_matching_ratio > 0.75:
                ProductFilterMatched = ProductFilters.objects.filter(ProductUrl=product.Url)[0]
                Filters_List = self.FindFilter(ProductFilterMatched, Filters_List, product.Id, groupId)
                print('productUrlMain', productUrlMain)
                print('product.Url', product.Url)
                print('productUrl filter', ProductFilters.objects.filter(ProductUrl=productUrlMain)[0].Id)
                print('product.Url filter', ProductFilters.objects.filter(ProductUrl=product.Url)[0].Id)
                product_matched_data.extend(
                    [product.Id, product.Name, product.Description, product.Brand, product.Url, Filters_List])
        return product_matched_data

    def SavingComparisonMatchedFilter(self, product_matched_data):
        DateUpdated = ''
        if MatchedProduct.objects.filter(ProductId=Product.objects.filter(Id=product_matched_data[0][0])[0]).exists():
            Groupdata = \
            MatchedProduct.objects.filter(ProductId=Product.objects.filter(Id=product_matched_data[0][0])[0])[0]
            GroupId = Groupdata.GroupId
            DateUpdated = Groupdata.DateUpdated
            MatchedProduct.objects.filter(GroupId=GroupId).delete()
        if not DateUpdated:
            DateUpdated = datetime.datetime.now()
        for pro in product_matched_data:
            MatchedProduct(ProductId=Product.objects.filter(Id=pro[0])[0], GroupId=pro[1], Character=pro[2],
                           Closure=pro[3], DressLength=pro[4], DressStyle=pro[5],
                           Embellishment=pro[6], Feature=pro[7], FitType=pro[8], GarmentCare=pro[9], Material=pro[10],
                           Neckline=pro[11],
                           Occasion=pro[12], Pattern=pro[13], FasteningType=pro[14], CuffStyle=pro[15], Collar=pro[16],
                           SleveesLength=pro[17],
                           SleveesType=pro[18], Themes=pro[19], Season=pro[20], ShowOnly=pro[21],
                           DateCreated=datetime.datetime.now(), DateUpdated=DateUpdated
                           ).save()

    def SavingSimilarMatchedFilter(self, product_matched_data):
        DateUpdated = ''
        if SimilarProduct.objects.filter(ProductId=Product.objects.filter(Id=product_matched_data[0][0])[0]).exists():
            Groupdata = \
            SimilarProduct.objects.filter(ProductId=Product.objects.filter(Id=product_matched_data[0][0])[0])[0]
            GroupId = Groupdata.GroupId
            DateUpdated = Groupdata.DateUpdated  # Verify this
            SimilarProduct.objects.filter(GroupId=GroupId).delete()
        if not DateUpdated:
            DateUpdated = datetime.datetime.now()
        for pro in product_matched_data:
            SimilarProduct(ProductId=Product.objects.filter(Id=pro[0])[0], GroupId=pro[1], Character=pro[2],
                           Closure=pro[3], DressLength=pro[4], DressStyle=pro[5],
                           Embellishment=pro[6], Feature=pro[7], FitType=pro[8], GarmentCare=pro[9], Material=pro[10],
                           Neckline=pro[11],
                           Occasion=pro[12], Pattern=pro[13], FasteningType=pro[14], CuffStyle=pro[15], Collar=pro[16],
                           SleveesLength=pro[17],
                           SleveesType=pro[18], Themes=pro[19], Season=pro[20], ShowOnly=pro[21],
                           DateCreated=datetime.datetime.now(), DateUpdated=DateUpdated
                           ).save()

    def FindMatching(self):
        all_products = Product.objects.filter(Deleted=0)
        for product in all_products:
            product_name_w_o_color = ''
            if ProductSize.objects.filter((~Q(ProductPrice=0)), ProductId=product.Id).count() >= 1:
                print('size variation exists')
            else:
                SizeData = ProductSize.objects.filter(ProductId=product.Id)
                for color in SizeData:
                    if color.Color:
                        product_name_w_o_color = (product.Name).replace(color.Color, '')
            product_matched_data_comparison = self.SearchSameProductInDb(product.Id, product.Name,
                                                                         product_name_w_o_color, product.Brand,
                                                                         product.Url, product.StoreId.Id, 'Comparison')
            if product_matched_data_comparison:
                self.SavingComparisonMatchedFilter(product_matched_data_comparison[5])
            product_matched_data_similarity = self.SearchSameProductInDb(product.Id, product.Name,
                                                                         product_name_w_o_color, product.Brand,
                                                                         product.Url, product.StoreId.Id, 'Similarity')
            print('_____________________________________')
            if product_matched_data_similarity:
                self.SavingSimilarMatchedFilter(product_matched_data_similarity[5])
            self.group_id += 1
            self.similar_group_id += 1


ProductMatchingClass().FindMatching()
