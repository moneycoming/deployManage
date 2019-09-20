from django.conf.urls import url
from zentao import views

urlpatterns = [
    url(r'^api/productBugPercent', views.get_productBugPercent, name='productBugPercent'),
    url(r'^api/productTaskPercent', views.get_productTaskPercent, name='productTaskPercent'),
    url(r'^api/productTaskStatusPercent', views.get_productTaskStatusPercent, name='productTaskStatusPercent'),
    url(r'^api/productScorePercent', views.get_productScorePercent, name='productScorePercent'),
]
