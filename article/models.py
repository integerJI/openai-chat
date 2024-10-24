from django.db import models

class Article(models.Model):
    id = models.AutoField(primary_key=True)
    category = models.CharField(max_length=100)
    post_date = models.DateField()
    source = models.CharField(max_length=100)
    title = models.CharField(max_length=255)
    thumbnail = models.URLField(max_length=500)
    url = models.URLField(max_length=500)
    regist_time = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title