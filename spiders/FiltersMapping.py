import os
from unicodedata import category

import django

from FashionStores.filters import *

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "FashionStores.settings")
django.setup()
import re
import datetime
from py_linq import Enumerable
from FashionStores.models import *


def APIFilters(url, name, category, description):
    gender = []
    valueList = []
    regexTexts = []
    filterList = []
    materialPCT = []
    categoryFilter = []
    print(url, name, category, description)

    kidsPattern = r"\b((Girl|Boy)(-|')?(s?))\b"
    adultPattern = r"\b((Women|Woman|Men|Man)(-|')?(s?))\b"
    babyPattern = r"\b(Baby(\s|-)(Boy|Girl)(-|')?(s?))\b"

    if re.search(adultPattern, category, re.IGNORECASE):
        gender = re.search(adultPattern, category, re.IGNORECASE).group(0)
    elif re.search(kidsPattern, category, re.IGNORECASE) and not re.search(r"\b(Baby(-|')?(s?))\b", category,
                                                                           re.IGNORECASE):
        gender = re.search(kidsPattern, category, re.IGNORECASE).group(0)
    elif re.search(babyPattern, category, re.IGNORECASE):
        gender = re.search(babyPattern, category, re.IGNORECASE).group(0)
    else:
        raise Exception("Gender Not Found")

    gender = str(re.sub(r"(-|\')", '', gender).strip().lower())
    if 'man' in gender or 'men' in gender:
        gender = gender.replace('man', 'men').strip().rstrip('s')
    elif not gender.endswith('s'):
        gender = gender + 's'

    gender = gender.title()

    """ checking the product"""
    product_type = re.search(r'dress|jeans', name + " " + category, re.IGNORECASE).group(0).lower()


    # Pre-defined list of filterTypes (for correct mapping of ProductFilters & ProductFilterIDs)
    filterTypes = ['Character', 'Closure', 'DressLength', 'DressStyle', 'Embellishment', 'Feature', 'FitType',
                   'GarmentCare', 'Material', 'Neckline', 'Occasion', 'Pattern', 'FasteningType', 'CuffStyle', 'Collar',
                   'SleeveLength', 'SleeveType', 'Theme', 'Season', "PocketType", "Rise", 'ShowOnly']

    filterDict = {'Character': Character, 'Closure': Closure, 'DressLength': filtersdic[product_type]['DressLength'], 'DressStyle': filtersdic[product_type]['DressStyle'],
                  'Embellishment': Embellishment, 'Feature': Feature, 'FitType': FitType, 'GarmentCare': GarmentCare,
                  'Material': Material, 'Neckline': Neckline, 'Occasion': Occasion, 'Pattern': Pattern,
                  'FasteningType': FasteningType, 'CuffStyle': CuffStyle, 'Collar': Collar,
                  'SleeveLength': filtersdic[product_type]['SleeveLength'], 'SleeveType': filtersdic[product_type]['SleeveType'], 'Theme': Theme, 'Season': Season,
                  "PocketType": filtersdic[product_type]['PocketType'], "Rise": filtersdic[product_type]['Rise'], 'ShowOnly': ShowOnly}

    regexTexts.extend([name, category, description])
    for filterType in filterTypes:
        if filterType == 'GarmentCare' or filterType == 'Season':
            genderFilters = filterDict[filterType]
        else:
            genderFilters = Enumerable(filterDict[filterType]).where(lambda x: x[0] == gender).select(
                lambda y: y).to_list()

        filterList = FilterNamesAndKeys(genderFilters, filterType, regexTexts, filterList, materialPCT)

    productFilter, productFilterIDs = GetValues(filterList)

    genderID = Enumerable(Category).where(lambda x: x[0] == gender).select(lambda y: y[1]).first_or_default()
    categoryList = Enumerable(Category).where(lambda x: x[0] == gender).select(lambda y: y).to_list()

    if re.search(r"\b(Infant|New((\s|-)?)Born)(-|')?(s?)\b", " ".join(regexTexts), re.IGNORECASE):
        for i in re.finditer(r"\b(Infant|New((\s|-)?)Born)(-|')?(s?)\b", " ".join(regexTexts), re.IGNORECASE):
            valueList.append((i.group(0), Enumerable(categoryList).where(lambda y: y[2] == i.group(0)).select(
                lambda y: y[3]).first_or_default()))
    elif productFilter[3] != 'Not Specified':
        for filId in str(productFilterIDs[3]).split(','):
            filName = Enumerable(filtersdic[product_type]['DressStyle']).where(lambda x: x[3] == filId).select(
                lambda y: y[2]).first_or_default()
            catList = Enumerable(categoryList).where(lambda x: filName in x[4] or x[2] == filName).to_list()
            for catTuple in catList:
                valueList.append((catTuple[2], catTuple[3]))
    else:
        for i in ['Casual', 'Formal']:
            valueList.append((i, Enumerable(categoryList).where(lambda y: y[2] == i).select(
                lambda y: y[3]).first_or_default()))

    categoryFilter.append(list(set(valueList)))
    catPro, catApi = GetValues(categoryFilter)

    if productFilter[8] != 'Not Specified':
        materialPCT = list(set(materialPCT))
        percentageValues = Enumerable(materialPCT).where(lambda x: '%' in x[0]).to_list()
        if percentageValues:
            materialList = []
            for i in percentageValues:
                percentage = re.search(r'\d+( |)%', i[0]).group(0)
                existingMaterial = Enumerable(materialList).where(lambda x: str(x[1]) == str(i[1])).first_or_default()
                if not existingMaterial:
                    materialList.append((percentage.replace('%', ''), i[1]))
            nonPercentageValues = Enumerable(materialPCT).where(lambda x: not '%' in x[0]).to_list()
            for j in nonPercentageValues:
                existingMaterial = Enumerable(materialList).where(lambda x: str(x[1]) == str(j[1])).first_or_default()
                if not existingMaterial:
                    materialList.append(('0', j[1]))
            percentageData = ','.join(Enumerable(materialList).select(lambda x: x[0]).to_list())
            percentageID = ','.join(Enumerable(materialList).select(lambda x: x[1]).to_list())
        else:
            zeroPercentages = []
            dataLen = len(list(set(Enumerable(materialPCT).select(lambda x: x[0]).to_list())))
            for i in range(dataLen):
                zeroPercentages.append('0')
            percentageData = ','.join(Enumerable(zeroPercentages).select(lambda x: x[0]).to_list())
            percentageID = ','.join(list(set(Enumerable(materialPCT).select(lambda x: x[1]).to_list())))
    else:
        percentageData = ''
        percentageID = productFilterIDs[8]
    if catPro and catApi:
        a = catPro[0]
        b = catApi[0]
    else:
        a = ''
        b = ''

    if ProductFilters.objects.filter(ProductUrl=url).exists():
        ProductFilters.objects.filter(ProductUrl=url).update(ProductUrl=url, Character=productFilter[0],
                                                             Closure=productFilter[1],
                                                             DressLength=productFilter[2], DressStyle=productFilter[3],
                                                             Embellishment=productFilter[4], Feature=productFilter[5],
                                                             FitType=productFilter[6], GarmentCare=productFilter[7],
                                                             Material=productFilter[8], Neckline=productFilter[9],
                                                             Occasion=productFilter[10], Pattern=productFilter[11],
                                                             FasteningType=productFilter[12],
                                                             CuffStyle=productFilter[13],
                                                             Collar=productFilter[14], SleeveLength=productFilter[15],
                                                             SleeveType=productFilter[16], Themes=productFilter[17],
                                                             Season=productFilter[18],
                                                             PocketType=productFilter[19],
                                                             Rise=productFilter[20],
                                                             ShowOnly=productFilter[21],
                                                             Category=a, ParentCategory=gender,
                                                             DateUpdated=datetime.datetime.now())
    else:
        ProductFilters(ProductUrl=url, Character=productFilter[0],
                       Closure=productFilter[1],
                       DressLength=productFilter[2], DressStyle=productFilter[3],
                       Embellishment=productFilter[4], Feature=productFilter[5],
                       FitType=productFilter[6], GarmentCare=productFilter[7],
                       Material=productFilter[8], Neckline=productFilter[9],
                       Occasion=productFilter[10], Pattern=productFilter[11],
                       FasteningType=productFilter[12],
                       CuffStyle=productFilter[13],
                       Collar=productFilter[14], SleeveLength=productFilter[15],
                       SleeveType=productFilter[16], Themes=productFilter[17],
                       Season=productFilter[18], PocketType=productFilter[19],Rise=productFilter[20], ShowOnly=productFilter[21],
                       Category=a, ParentCategory=gender).save()

    if ProductFilterIDs.objects.filter(ProductUrl=url).exists():
        ProductFilterIDs.objects.filter(ProductUrl=url).update(ProductUrl=url, Character=str(productFilterIDs[0]),
                                                               Closure=str(productFilterIDs[1]),
                                                               DressLength=str(productFilterIDs[2]),
                                                               DressStyle=productFilterIDs[3],
                                                               Embellishment=str(productFilterIDs[4]),
                                                               Feature=str(productFilterIDs[5]),
                                                               FitType=str(productFilterIDs[6]),
                                                               GarmentCare=str(productFilterIDs[7]),
                                                               Material=str(percentageID),
                                                               MaterialPercentage=str(percentageData),
                                                               Neckline=str(productFilterIDs[9]),
                                                               Occasion=str(productFilterIDs[10]),
                                                               Pattern=str(productFilterIDs[11]),
                                                               FasteningType=str(productFilterIDs[12]),
                                                               CuffStyle=str(productFilterIDs[13]),
                                                               Collar=str(productFilterIDs[14]),
                                                               SleeveLength=str(productFilterIDs[15]),
                                                               SleeveType=str(productFilterIDs[16]),
                                                               Themes=str(productFilterIDs[17]),
                                                               Season=str(productFilterIDs[18]),
                                                               PocketType=productFilter[19],
                                                               Rise=productFilter[20],
                                                               ShowOnly=str(productFilterIDs[21]),
                                                               Category=str(b),
                                                               ParentCategory=str(genderID),
                                                               DateUpdated=datetime.datetime.now())
    else:
        ProductFilterIDs(ProductUrl=url, Character=str(productFilterIDs[0]),
                         Closure=str(productFilterIDs[1]),
                         DressLength=str(productFilterIDs[2]),
                         DressStyle=productFilterIDs[3],
                         Embellishment=str(productFilterIDs[4]),
                         Feature=str(productFilterIDs[5]),
                         FitType=str(productFilterIDs[6]),
                         GarmentCare=str(productFilterIDs[7]),
                         Material=str(percentageID),
                         MaterialPercentage=str(percentageData),
                         Neckline=str(productFilterIDs[9]),
                         Occasion=str(productFilterIDs[10]), Pattern=str(productFilterIDs[11]),
                         FasteningType=str(productFilterIDs[12]),
                         CuffStyle=str(productFilterIDs[13]), Collar=str(productFilterIDs[14]),
                         SleeveLength=str(productFilterIDs[15]),
                         SleeveType=str(productFilterIDs[16]),
                         Themes=str(productFilterIDs[17]),
                         Season=str(productFilterIDs[18]),
                         PocketType=productFilter[19],
                         Rise=productFilter[20],
                         ShowOnly=str(productFilterIDs[21]),
                         Category=str(b),
                         ParentCategory=str(genderID)).save()

    pass


def GetValues(filtersList):
    apiFil = []
    productFil = []
    for fil in filtersList:
        unSpecified = list(set(Enumerable(fil).where(lambda x: x[0] == 'Not Specified').to_list()))
        matchedResult = Enumerable(fil).where(lambda x: x[0] != 'Not Specified').to_list()
        if unSpecified and not matchedResult:
            productFil.append(unSpecified[0][0])
            apiFil.append(unSpecified[0][1])
        elif matchedResult:
            if len(matchedResult) == 1:
                for matched in matchedResult:
                    productFil.append(matched[0])
                    apiFil.append(matched[1])
            else:
                multipro = ','.join(list(set(Enumerable(matchedResult).select(lambda x: x[0]).to_list())))
                multiApi = ','.join(list(set(Enumerable(matchedResult).select(lambda x: x[1]).to_list())))
                productFil.append(multipro)
                apiFil.append(multiApi)

    return [productFil, apiFil]


def FilterNamesAndKeys(genderFilters, filterType, regexTexts, filterList, materialPCT):
    if "ShowOnly" in filterType:
        filterKeyWords = []
        filterNames = genderFilters
    else:
        filterNames = Enumerable(genderFilters).select(lambda y: y[2]).to_list()
        filterKeyWords = list(filter(None, Enumerable(genderFilters).select(lambda y: y[4]).to_list()))

    matchedFilters = []
    for regexText in regexTexts:
        matchedFilters.append(RegexMappingNames(genderFilters, regexText, filterNames, filterType, materialPCT))
        matchedFilters.append(RegexMappingKeys(genderFilters, regexText, filterKeyWords))

    filterList.append(sum(matchedFilters, []))
    return filterList


def RegexMappingNames(filterList, regexText, regexValues, filterType, materialPCT):
    valueList = []
    matchedData = []
    materialData = []
    for i in regexValues:
        if 'Material' in filterType:
            regexPattern = r'\b((' + i.replace(
                "/", "\/").replace("% ", "(%|(%) )").replace(" ",
                                                             "( |-)") + r')((line)?)(s|ed)?(?!( |-)?Sleeve))\b(( |)?(\w+))( |)\d+( |)%|\b(\d+( |)%(( |)?(\w+)?))?((' + i.replace(
                "/", "\/").replace("% ", "(%|(%) )").replace(" ",
                                                             "( |-)") + r')((line)?)(s|ed)?(?!( |-)?Sleeve))\b'
        else:
            regexPattern = r'\b((' + i.replace("/", "\/").replace("% ", "(%|(%) )").replace(" ",
                                                                                            "( |-)") + r')((line)?)(s|ed)?(?!( |-)?Sleeve))\b'

        for m in re.finditer(regexPattern, regexText, re.IGNORECASE):
            if 'Material' in filterType:
                materialData.append(m.group(0))
            else:
                matchedData.append(i)

    if matchedData:
        matchedData = set(matchedData)
        for matchedStr in matchedData:
            matchedValue = Enumerable(filterList).where(
                lambda x: x[2] == matchedStr).select(
                lambda y: y[3]).first_or_default()
            valueList.append((matchedStr, matchedValue))
    elif materialData:
        materialData = set(materialData)
        for materialStr in materialData:
            for i in filterList:
                if re.search(str(i[2]), materialStr, re.IGNORECASE):
                    materialPCT.append((materialStr, i[3]))
                    valueList.append((materialStr, i[3]))
    else:
        matchedStr = 'Not Specified'
        matchedValue = Enumerable(filterList).where(
            lambda x: x[2] == matchedStr).select(
            lambda y: y[3]).first_or_default()
        valueList.append((matchedStr, matchedValue))

    return valueList


def RegexMappingKeys(filterList, regexText, regexValues):
    valueList = []
    matchedData = []
    for i in regexValues:
        iPattern = r'\b((' + i.replace("/", "\/").replace("% ", "(%|(%) )").replace(" ",
                                                                                    "( |-)") + r')((line)?)(s|ed)?(?!( |-)?Sleeve))\b'
        if re.search(', ', i):
            keyWordsList = str(i).split(", ")
            for j in keyWordsList:
                jPattern = r'\b((' + j.replace("/", "\/").replace("% ", "(%|(%) )").replace(" ",
                                                                                            "( |-)") + r')((line)?)(s|ed)?(?!( |-)?Sleeve))\b'

                for k in re.finditer(jPattern, regexText, re.IGNORECASE):
                    matchedData.append(j)
        else:
            for m in re.finditer(iPattern, regexText, re.IGNORECASE):
                matchedData.append(i)

    if matchedData:
        matchedData = set(matchedData)
        for matchedStr in matchedData:
            for i in filterList:
                if re.search(matchedStr, str(i[4])):
                    valueList.append((matchedStr, i[3]))
    else:
        matchedStr = 'Not Specified'
        matchedValue = Enumerable(filterList).where(
            lambda x: x[2] == matchedStr).select(
            lambda y: y[3]).first_or_default()
        valueList.append((matchedStr, matchedValue))

    return valueList
