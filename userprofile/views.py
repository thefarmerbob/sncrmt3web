from django.shortcuts import render, redirect
from django.contrib.auth import logout, login

from .models import Userprofile
from .forms import CustomUserCreationForm

def signup(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)

        if form.is_valid():
            user = form.save()
            Userprofile.objects.create(user=user)
            login(request, user)  # Log in the user immediately after signup
            return redirect('applications_list')  # Redirect to applications page
        else:
            print('Form errors:', form.errors)
        
    else:
        form = CustomUserCreationForm()

    return render(request, 'userprofile/signup.html', {
        'form': form
    })

def logout_user(request):
    logout(request)  
    return redirect('login')
