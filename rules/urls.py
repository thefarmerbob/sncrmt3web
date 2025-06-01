from django.urls import path
from . import views

app_name = 'rules'

urlpatterns = [
    path('', views.rules_list, name='rules_list'),
] 