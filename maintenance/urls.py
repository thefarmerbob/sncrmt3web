from django.urls import path
from . import views

app_name = 'maintenance'

urlpatterns = [
    path('create/', views.maintenance_create, name='maintenance_create'),
    path('<int:pk>/', views.maintenance_detail, name='maintenance_detail'),
] 