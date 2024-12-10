from django.shortcuts import render
from Client.models import ClientUser
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login
from django.shortcuts import redirect
from django.contrib.auth.views import LogoutView
from django.urls import reverse_lazy, reverse

@login_required(login_url='Client:login')
def homeView(request):
    user = ClientUser.objects.get(username=request.user.username, password=request.user.password)
    
    # Access the associated client (it's already the instance, no need for 'pk=user.client')
    client = user.client  # This is the associated Client instance
    engagements = client.engagements.all()
    return render(request, 'Client/homepage.html', {'engagements':engagements})

def ClientLogin(request):
    if request.method == 'POST':
        # Authenticating the person trying to log in
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None and user.is_authenticated:
            login(request, user)
            return redirect('Client:home')
        else:
            return render(request, 'Client/login.html', {'error':'Invalid Credentitals'})
    return render(request, 'Client/login.html')

def aboutView(request):
    return render(request, 'Client/about.html')

class ClientLogoutView(LogoutView):
    next_page = reverse_lazy('Client:home')