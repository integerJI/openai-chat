from rest_framework import generics
from rest_framework import status
from .models import Article
from .serializers import ArticleSerializer
from mychatbot.utils import custom_response

# Article 리스트를 불러오고, 생성하는 클래스
class ArticleListCreateView(generics.ListCreateAPIView):
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer

    def get(self, request, *args, **kwargs):
        articles = self.get_queryset()
        serializer = self.get_serializer(articles, many=True)
        return custom_response(data=serializer.data, code=200, message="success", status_code=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return custom_response(data=serializer.data, code=201, message="Article created successfully", status_code=status.HTTP_201_CREATED)
        return custom_response(data=serializer.errors, code=400, message="Invalid data", status_code=status.HTTP_400_BAD_REQUEST)

# 특정 Article 정보를 가져오고, 수정하고, 삭제하는 클래스
class ArticleDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer

    def get(self, request, *args, **kwargs):
        article = self.get_object()
        serializer = self.get_serializer(article)
        return custom_response(data=serializer.data, code=200, message="success", status_code=status.HTTP_200_OK)

    def put(self, request, *args, **kwargs):
        article = self.get_object()
        serializer = self.get_serializer(article, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return custom_response(data=serializer.data, code=200, message="Article updated successfully", status_code=status.HTTP_200_OK)
        return custom_response(data=serializer.errors, code=400, message="Invalid data", status_code=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, *args, **kwargs):
        article = self.get_object()
        article.delete()
        return custom_response(data=None, code=204, message="Article deleted successfully", status_code=status.HTTP_204_NO_CONTENT)