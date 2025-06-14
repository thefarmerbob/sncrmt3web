from django.urls import path
from . import views

urlpatterns = [
    path('', views.applications_list, name='applications_list'),
    path('new/', views.applications, name='applications'),
    path('availability-matrix/', views.availability_matrix, name='availability_matrix'),
    path('<int:pk>/', views.application_detail, name='application_detail'),
    path('<int:pk>/edit/', views.edit_application, name='application_edit'),
    path('step2/', views.application_step2, name='application_step2'),
    path('reintroduction-question/', views.reintroduction_question, name='reintroduction_question'),
    path('reintroduction-form/', views.reintroduction_form, name='reintroduction_form'),
    path('success/', views.application_success, name='application_success'),
    path('available-chapters/', views.available_chapters, name='available_chapters'),
    path('<int:pk>/withdraw/', views.withdraw_application, name='withdraw_application'),
]
