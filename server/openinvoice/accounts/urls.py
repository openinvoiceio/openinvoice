from django.urls import path

from .views import (
    AccountListCreateAPIView,
    AccountRetrieveUpdateDestroyAPIView,
    AccountSwitchAPIView,
    BusinessProfileListCreateAPIView,
    BusinessProfileRetrieveUpdateDestroyAPIView,
    BusinessProfileTaxIdCreateAPIView,
    BusinessProfileTaxIdDestroyAPIView,
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
    path("business-profiles", BusinessProfileListCreateAPIView.as_view()),
    path("business-profiles/<uuid:pk>", BusinessProfileRetrieveUpdateDestroyAPIView.as_view()),
    path("business-profiles/<uuid:pk>/tax-ids", BusinessProfileTaxIdCreateAPIView.as_view()),
    path(
        "business-profiles/<uuid:business_profile_id>/tax-ids/<uuid:pk>",
        BusinessProfileTaxIdDestroyAPIView.as_view(),
    ),
    path("accounts/<uuid:account_id>/members", MemberListAPIView.as_view()),
    path("accounts/<uuid:account_id>/members/<int:pk>", MemberRetrieveDestroyAPIView.as_view()),
    path("invitations", InvitationListCreateAPIView.as_view()),
    path("invitations/<uuid:pk>", InvitationRetrieveDestroyAPIView.as_view()),
    path("invitations/accept", InvitationAcceptAPIView.as_view()),
]
