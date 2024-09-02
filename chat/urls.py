# chat/urls.py
from django.urls import path
from .views import ChatSessionView, MessageView, ChatView, ChatSessionDetailView

urlpatterns = [
    path('', ChatView.as_view(), name='chat'),
    path('prompt/', ChatSessionView.as_view(), name='create-session'),
    path('prompt/<str:session_id>/', ChatSessionDetailView.as_view(), name='session-detail'),
    path('prompt/<str:session_id>/messages/', MessageView.as_view(), name='messages'),
]
