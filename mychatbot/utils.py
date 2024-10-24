from rest_framework.response import Response
from rest_framework import status

def custom_response(data=None, code=None, message=None, status_code=status.HTTP_200_OK):
    """
    Custom response format.
    
    :param data: Response data to include.
    :param code: Custom status code for the response.
    :param message: Message corresponding to the response code.
    :param status_code: HTTP status code to be returned.
    :return: Formatted Response object.
    """
    # 기본값 설정
    if code is None:
        code = 200
    if message is None:
        message = "success"
    
    response_structure = {
        "code": code,
        "message": message,
        "data": data if data is not None else {}
    }
    return Response(response_structure, status=status_code)