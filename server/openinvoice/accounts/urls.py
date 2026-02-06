from django.urls import path

from .views import (
    AccountListCreateAPIView,
    AccountRetrieveUpdateDestroyAPIView,
    AccountSwitchAPIView,
    AccountTaxIdCreateAPIView,
    AccountTaxIdDestroyAPIView,
    BusinessProfileListCreateAPIView,
    BusinessProfileRetrieveUpdateDestroyAPIView,
    InvitationAcceptAPIView,
    InvitationListCreateAPIView,
    InvitationRetrieveDestroyAPIView,
    MemberListAPIView,
    MemberRetrieveDestroyAPIView,
)

urlpatterns = [
    path("accounts", AccountListCreateAPIView.as_view()),
    path("accounts/<uuid:pk>", AccountRetrieveUpdateDestroyAPIView.as_view()),
    path("accounts/<uuid:pk>/switch", AccountSwitchAPIView.as_view()),
    path("accounts/<uuid:account_id>/tax-ids", AccountTaxIdCreateAPIView.as_view()),
    path(
        "accounts/<uuid:account_id>/tax-ids/<uuid:pk>",
        AccountTaxIdDestroyAPIView.as_view(),
    ),
    path("business-profiles", BusinessProfileListCreateAPIView.as_view()),
    path("business-profiles/<uuid:pk>", BusinessProfileRetrieveUpdateDestroyAPIView.as_view()),
    path("accounts/<uuid:account_id>/members", MemberListAPIView.as_view()),
    path("accounts/<uuid:account_id>/members/<int:pk>", MemberRetrieveDestroyAPIView.as_view()),
    path("invitations", InvitationListCreateAPIView.as_view()),
    path("invitations/<uuid:pk>", InvitationRetrieveDestroyAPIView.as_view()),
    path("invitations/accept", InvitationAcceptAPIView.as_view()),
]
