from django.urls import path

from .views import GrossRevenueAPIView, OverdueBalanceAPIView

urlpatterns = [
    path("analytics/gross-revenue", GrossRevenueAPIView.as_view()),
    path("analytics/overdue-balance", OverdueBalanceAPIView.as_view()),
]
