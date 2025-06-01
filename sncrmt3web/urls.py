from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views
from core.views import join, core_router
from userprofile.views import signup

urlpatterns = [
    path('', core_router, name='core_router'),
    path('admin/', admin.site.urls),
    path('signup/', signup, name='signup'),
    path('login/', views.LoginView.as_view(template_name='userprofile/login.html'), name='login'),
    path('join/', join, name='join'),
    
    # Password reset URLs
    path('password-reset/', 
         views.PasswordResetView.as_view(
             template_name='userprofile/password_reset.html',
             email_template_name='userprofile/password_reset_email.html',
             subject_template_name='userprofile/password_reset_subject.txt'
         ), 
         name='password_reset'),
    path('password-reset/done/', 
         views.PasswordResetDoneView.as_view(template_name='userprofile/password_reset_done.html'), 
         name='password_reset_done'),
    path('reset/<uidb64>/<token>/', 
         views.PasswordResetConfirmView.as_view(template_name='userprofile/password_reset_confirm.html'), 
         name='password_reset_confirm'),
    path('reset/done/', 
         views.PasswordResetCompleteView.as_view(template_name='userprofile/password_reset_complete.html'), 
         name='password_reset_complete'),
    
    path('userprofile/', include('userprofile.urls')),
    path('dashboard/', include('dashboard.urls')),
    path('dashboard/applications/', include('applications.urls')),
    path('dashboard/chapter-transfers/', include('chapter_transfers.urls')),
    path('rules/', include('rules.urls')),
    path('payments/', include('payments.urls')),
    path('maintenance/', include('maintenance.urls')),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
