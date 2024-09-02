# chat/views.py
import openai
import certifi
import requests
from django.conf import settings
from django.shortcuts import render, get_object_or_404, redirect
from django.views import View
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import ChatSession, Message
from .serializers import ChatSessionSerializer, MessageSerializer
import uuid
from drf_yasg.utils import swagger_auto_schema
from rest_framework import serializers
from requests.packages.urllib3.exceptions import InsecureRequestWarning

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

class MessageRequestSerializer(serializers.Serializer):
    message = serializers.CharField()

class MessageView(APIView):
    @swagger_auto_schema(
        request_body=MessageRequestSerializer,
        responses={201: MessageSerializer, 400: 'Bad Request', 500: 'Internal Server Error'}
    )
    def post(self, request, session_id):
        chat_session = get_object_or_404(ChatSession, session_id=session_id)
        user_message = request.data.get('message')

        if not user_message:
            return Response({"error": "User message cannot be empty."}, status=status.HTTP_400_BAD_REQUEST)

        # 사용자 메시지 저장
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
                # 외부 API 호출 - 체크리스트 생성 (SSL 검증 무시)
                response = requests.post(
                    "https://s-class.koyeb.app/v1/checklists",
                    headers={
                        "accept": "application/json",
                        "Content-Type": "application/json"
                    },
                    json={"userId": session_id},
                    verify=False  # SSL 검증 무시
                )

                # 요청이 성공했는지 확인 (201 상태 코드 확인)
                if response.status_code == 201:
                    checklistId = response.json().get("id")
                    
                    # 체크박스 항목 추가
                    for title in checklist_titles:
                        checkbox_response = requests.post(
                            f"https://s-class.koyeb.app/v1/checklists/{checklistId}/checkboxes",
                            headers={
                                "accept": "application/json",
                                "Content-Type": "application/json"
                            },
                            json={"checklistId": checklistId, "label": title, "userId": session_id},
                            verify=False  # SSL 검증 무시
                        )
                        if checkbox_response.status_code != 201:
                            return Response({"error": f"Failed to add checklist item: {title}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                    
                    # 최종 메시지 생성
                    bot_message = f"체크리스트가 생성되었습니다. 항목을 확인하려면 여기를 클릭하세요: https://s-class.koyeb.app/v1/checklists/{checklistId}/checkboxes"
                else:
                    return Response({"error": "Failed to create checklist."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            except Exception as e:
                # 예외 발생 시 로깅
                print("Exception during API call:", str(e))
                return Response({"error": "An error occurred while trying to create the checklist."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        else:
            # OpenAI API를 이용한 응답 생성
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
                return Response({"error": "Failed to get a response from OpenAI."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        if bot_message:
            bot_message_obj = Message.objects.create(chat_session=chat_session, message_text=bot_message, is_user=False)
            return Response(MessageSerializer(bot_message_obj).data, status=status.HTTP_201_CREATED)
        else:
            return Response({"error": "Empty response from OpenAI."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @swagger_auto_schema(
        responses={200: ChatSessionSerializer}
    )
    def get(self, request, session_id):
        chat_session = get_object_or_404(ChatSession, session_id=session_id)
        serializer = ChatSessionSerializer(chat_session)
        return Response(serializer.data)

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

class MessageRequestSerializer(serializers.Serializer):
    message = serializers.CharField()

class ChatSessionDetailView(View):
    def get(self, request, session_id):
        chat_session = get_object_or_404(ChatSession, session_id=session_id)
        messages = chat_session.messages.all()
        return render(request, 'chat/session_detail.html', {'session_id': session_id, 'messages': messages})
