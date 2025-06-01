from django.urls import path
from . import views

app_name = 'chapter_transfers'

urlpatterns = [
    path('', views.transfer_request_list, name='list'),
    path('create/', views.create_transfer_request, name='create'),
    path('<int:pk>/', views.transfer_request_detail, name='detail'),
] 