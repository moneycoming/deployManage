from django.conf.urls import url
from zentao import views

urlpatterns = [
    url(r'^api/sum', views.get_sum, name='sum'),
]
