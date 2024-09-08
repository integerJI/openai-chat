# utils.py
from rest_framework.response import Response
from rest_framework import status

def custom_response(data=None, status=status.HTTP_200_OK):
    return Response({"data": data}, status=status)