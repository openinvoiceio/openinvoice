from django.urls import path

from .views import (
    CouponListCreateAPIView,
    CouponRetrieveUpdateDestroyAPIView,
)

urlpatterns = [
    path("coupons", CouponListCreateAPIView.as_view()),
    path("coupons/<uuid:pk>", CouponRetrieveUpdateDestroyAPIView.as_view()),
]
