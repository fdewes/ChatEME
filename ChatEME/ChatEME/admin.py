from django.contrib import admin
from .models import ClassifierModel, CrawlRoot, WebPage 

# Register your models here.

admin.site.register(ClassifierModel)
admin.site.register(CrawlRoot)
admin.site.register(WebPage)