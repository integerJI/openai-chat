# chat/views.py
import openai
from django.conf import settings
from django.shortcuts import render, get_object_or_404, redirect
from django.views import View
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import ChatSession, Message
from .serializers import ChatSessionSerializer, MessageSerializer
import uuid

openai.api_key = settings.OPENAI_API_KEY

class ChatView(View):
    def get(self, request):
        return render(request, 'chat/index.html')

    def post(self, request):
        # 새로운 세션 생성
        session_id = str(uuid.uuid4())
        chat_session = ChatSession.objects.create(session_id=session_id)

        # 첫 번째 메시지 저장
        user_message = request.POST.get('message')
        if user_message:
            Message.objects.create(chat_session=chat_session, message_text=user_message, is_user=True)
            
            # OpenAI API를 이용한 응답 생성
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": user_message},
                ]
            )
            bot_message = response.choices[0].message['content'].strip()

            # 봇 메시지 저장
            Message.objects.create(chat_session=chat_session, message_text=bot_message, is_user=False)

        # 세션 상세 페이지로 리다이렉트
        return redirect(f'/api/session/{session_id}/')

class ChatSessionView(APIView):
    def post(self, request):
        session_id = str(uuid.uuid4())
        chat_session = ChatSession.objects.create(session_id=session_id)
        serializer = ChatSessionSerializer(chat_session)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class MessageView(APIView):
    def get(self, request, session_id):
        chat_session = get_object_or_404(ChatSession, session_id=session_id)
        serializer = ChatSessionSerializer(chat_session)
        return Response(serializer.data)

    def post(self, request, session_id):
        chat_session = get_object_or_404(ChatSession, session_id=session_id)
        user_message = request.data.get('message')
        
        # 사용자 메시지 저장
        Message.objects.create(chat_session=chat_session, message_text=user_message, is_user=True)
        
        # OpenAI API를 이용한 응답 생성
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": user_message},
            ]
        )
        bot_message = response.choices[0].message['content'].strip()

        # 봇 메시지 저장
        bot_message_obj = Message.objects.create(chat_session=chat_session, message_text=bot_message, is_user=False)

        return Response(MessageSerializer(bot_message_obj).data, status=status.HTTP_201_CREATED)

class ChatSessionDetailView(View):
    def get(self, request, session_id):
        chat_session = get_object_or_404(ChatSession, session_id=session_id)
        messages = chat_session.messages.all()
        return render(request, 'chat/session_detail.html', {'session_id': session_id, 'messages': messages})
