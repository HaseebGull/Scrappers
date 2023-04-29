import os, sys, django
try:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "FashionStores.settings")
    django.setup()
except:
    sys.path.append("E:\\JOB\\Github\\GithubAfterFilter\\")
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "FashionStores.settings")
    django.setup()
from FashionStores.models import MatchedProduct,SimilarProduct

class CheckDeletedProducts:
    def __init__(self):
        pass

    def DeleteOOS(self):
        for product in SimilarProduct.objects.all():
            if product.ProductId.Deleted==1:
                product.delete()
                
        for product in MatchedProduct.objects.all():
            if product.ProductId.Deleted == 1:
                product.delete()

CheckDeletedProducts().DeleteOOS()
