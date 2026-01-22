from django.urls import path

from .views import (
    CouponArchiveAPIView,
    CouponListCreateAPIView,
    CouponRestoreAPIView,
    CouponRetrieveUpdateDestroyAPIView,
)

urlpatterns = [
    path("coupons", CouponListCreateAPIView.as_view()),
    path("coupons/<uuid:pk>", CouponRetrieveUpdateDestroyAPIView.as_view()),
    path("coupons/<uuid:pk>/archive", CouponArchiveAPIView.as_view()),
    path("coupons/<uuid:pk>/restore", CouponRestoreAPIView.as_view()),
]
