from django.urls import path

from .views import (
    CreditNoteCommentDestroyAPIView,
    CreditNoteCommentsListCreateAPIView,
    CreditNoteIssueAPIView,
    CreditNoteLineCreateAPIView,
    CreditNoteLineTaxCreateAPIView,
    CreditNoteLineTaxDestroyAPIView,
    CreditNoteLineUpdateDestroyAPIView,
    CreditNoteListCreateAPIView,
    CreditNotePreviewAPIView,
    CreditNoteRetrieveUpdateDestroyAPIView,
    CreditNoteVoidAPIView,
)

urlpatterns = [
    path("credit-notes", CreditNoteListCreateAPIView.as_view()),
    path("credit-notes/<uuid:pk>", CreditNoteRetrieveUpdateDestroyAPIView.as_view()),
    path("credit-notes/<uuid:pk>/preview", CreditNotePreviewAPIView.as_view()),
    path("credit-notes/<uuid:credit_note_id>/comments", CreditNoteCommentsListCreateAPIView.as_view()),
    path("credit-notes/<uuid:credit_note_id>/comments/<uuid:pk>", CreditNoteCommentDestroyAPIView.as_view()),
    path("credit-note-lines", CreditNoteLineCreateAPIView.as_view()),
    path("credit-note-lines/<uuid:pk>", CreditNoteLineUpdateDestroyAPIView.as_view()),
    path("credit-note-lines/<uuid:line_id>/taxes", CreditNoteLineTaxCreateAPIView.as_view()),
    path(
        "credit-note-lines/<uuid:line_id>/taxes/<uuid:pk>",
        CreditNoteLineTaxDestroyAPIView.as_view(),
    ),
    path("credit-notes/<uuid:pk>/issue", CreditNoteIssueAPIView.as_view()),
    path("credit-notes/<uuid:pk>/void", CreditNoteVoidAPIView.as_view()),
]
