from django.contrib import admin
from django.urls import path
from .views import get_latest_filings

urlpatterns = [
    path('getLatestFilings/', get_latest_filings),
    #path('getSpecificFiling/', admin.site.urls)
]