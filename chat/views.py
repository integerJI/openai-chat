# chat/views.py
import openai
import certifi
import requests
from django.conf import settings
from django.shortcuts import render, get_object_or_404, redirect
from django.views import View
from rest_framework.views import APIView
from .models import ChatSession, Message
from .serializers import ChatSessionSerializer, MessageSerializer
import uuid
from drf_yasg.utils import swagger_auto_schema
from rest_framework import serializers
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from mychatbot.utils import custom_response
from rest_framework import status

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

class MessageRequestSerializer(serializers.Serializer):
    message = serializers.CharField()

class MessageView(APIView):
    @swagger_auto_schema(
        request_body=MessageRequestSerializer,
        responses={201: MessageSerializer, 400: 'Bad Request', 500: 'Internal Server Error'}
    )
    def post(self, request, session_id):
        # session_id로 ChatSession을 가져오고, 해당 session의 userId를 사용
        chat_session = get_object_or_404(ChatSession, session_id=session_id)
        user_message = request.data.get('message')

        if not user_message:
            return custom_response({"error": "User message cannot be empty."}, status=status.HTTP_400_BAD_REQUEST)

        # ChatSession에서 userId를 추출
        user_id = chat_session.user_id

        Message.objects.create(chat_session=chat_session, message_text=user_message, is_user=True)

        if "체크리스트" in user_message.lower():
            checklist_titles = [
                "이메일 확인",
                "일일 계획 설정",
                "회의 준비",
                "업무 수행",
                "업무일지 작성",
                "일일 리포트 전송",
                "당일까지의 거래 및 업무 확인"
            ]

            try:
                response = requests.post(
                    "https://s-class.koyeb.app/v1/checklists",
                    headers={
                        "accept": "application/json",
                        "Content-Type": "application/json"
                    },
                    json={"userId": user_id},  # userId 사용
                    verify=False
                )

                if response.status_code == 201:
                    checklistId = response.json().get("data", {}).get("id")
                    
                    for title in checklist_titles:
                        checkbox_response = requests.post(
                            f"https://s-class.koyeb.app/v1/checklists/{checklistId}/checkboxes",
                            headers={
                                "accept": "application/json",
                                "Content-Type": "application/json"
                            },
                            json={"checklistId": checklistId, "label": title, "userId": user_id},  # userId 사용
                            verify=False
                        )

                        if checkbox_response.status_code != 201:
                            return custom_response({"error": f"Failed to add checklist item: {checkbox_response.text}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                    
                    bot_message = f"체크리스트가 생성되었습니다. 항목을 확인하려면 여기를 클릭하세요: https://s-class.koyeb.app/v1/checklists/{checklistId}/checkboxes"
                else:
                    return custom_response({"error": "Failed to create checklist."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            except Exception as e:
                print("Exception during API call:", str(e))
                return custom_response({"error": "An error occurred while trying to create the checklist."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        else:
            try:
                response = openai.ChatCompletion.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant."},
                        {"role": "user", "content": user_message},
                    ]
                )
                bot_message = response.choices[0].message['content'].strip()
            except Exception as e:
                return custom_response({"error": "Failed to get a response from OpenAI."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        if bot_message:
            bot_message_obj = Message.objects.create(chat_session=chat_session, message_text=bot_message, is_user=False)
            return custom_response(MessageSerializer(bot_message_obj).data, status=status.HTTP_201_CREATED)
        else:
            return custom_response({"error": "Empty response from OpenAI."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    @swagger_auto_schema(
        responses={200: ChatSessionSerializer}
    )
    def get(self, request, session_id):
        chat_session = get_object_or_404(ChatSession, session_id=session_id)
        serializer = ChatSessionSerializer(chat_session)
        return custom_response(serializer.data)

openai.api_key = settings.OPENAI_API_KEY

class ChatView(View):
    def get(self, request):
        return render(request, 'chat/index.html')

    def post(self, request):
        session_id = str(uuid.uuid4())
        chat_session = ChatSession.objects.create(session_id=session_id)

        user_message = request.POST.get('message')
        if user_message:
            Message.objects.create(chat_session=chat_session, message_text=user_message, is_user=True)
            
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": user_message},
                ]
            )
            bot_message = response.choices[0].message['content'].strip()

            Message.objects.create(chat_session=chat_session, message_text=bot_message, is_user=False)

        return redirect(f'/v1/prompt/{session_id}/')
    
class ChatSessionRequestSerializer(serializers.Serializer):
    userId = serializers.CharField()

class ChatSessionListResponseSerializer(serializers.Serializer):
    session_ids = serializers.ListField(child=serializers.CharField())

class ChatSessionView(APIView):
    @swagger_auto_schema(
        request_body=ChatSessionRequestSerializer,
        responses={201: ChatSessionSerializer, 400: 'Bad Request'}
    )
    def post(self, request):
        session_id = str(uuid.uuid4())
        user_id = request.data.get('userId')

        if not user_id:
            return custom_response({"error": "userId is required."}, status=status.HTTP_400_BAD_REQUEST)

        chat_session = ChatSession.objects.create(session_id=session_id, user_id=user_id)
        serializer = ChatSessionSerializer(chat_session)

        return custom_response(serializer.data, status=status.HTTP_201_CREATED)

    @swagger_auto_schema(
        query_serializer=ChatSessionRequestSerializer,
        responses={200: ChatSessionListResponseSerializer, 400: 'Bad Request', 404: 'Not Found'}
    )
    def get(self, request):
        user_id = request.query_params.get('userId')

        if not user_id:
            return custom_response({"error": "userId is required."}, status=status.HTTP_400_BAD_REQUEST)

        session_ids = ChatSession.objects.filter(user_id=user_id).values_list('session_id', flat=True)

        if not session_ids:
            return custom_response({"error": "No sessions found for the given userId."}, status=status.HTTP_404_NOT_FOUND)

        return custom_response({"session_ids": list(session_ids)}, status=status.HTTP_200_OK)
        
class MessageRequestSerializer(serializers.Serializer):
    message = serializers.CharField()

class ChatSessionDetailView(View):
    def get(self, request, session_id):
        chat_session = get_object_or_404(ChatSession, session_id=session_id)
        messages = chat_session.messages.all()
        return render(request, 'chat/session_detail.html', {'session_id': session_id, 'messages': messages})
