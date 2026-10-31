from django.urls import path

from .views import CompanyDetailView, CompanyListView, MyCompanyView

urlpatterns = [
    path("", CompanyListView.as_view(), name="company-list"),
    path("me/", MyCompanyView.as_view(), name="company-me"),
    path("<int:pk>/", CompanyDetailView.as_view(), name="company-detail"),
]
