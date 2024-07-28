# chat/urls.py
from django.urls import path
from .views import ChatSessionView, MessageView, ChatView, ChatSessionDetailView

urlpatterns = [
    path('', ChatView.as_view(), name='chat'),
    path('session/', ChatSessionView.as_view(), name='create-session'),
    path('session/<str:session_id>/', ChatSessionDetailView.as_view(), name='session-detail'),
    path('session/<str:session_id>/messages/', MessageView.as_view(), name='messages'),
]
