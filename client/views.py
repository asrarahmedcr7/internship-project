from django.http import Http404
from django.shortcuts import render
from .models import Client
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate
from django.shortcuts import redirect
from .utils import generatePivot

@login_required(login_url='Client:login')
def homeView(request):
    client = Client.objects.get(username = request.user.username, password = request.user.password)
    engagements = client.engagements.all()
    return render(request, 'Client/homepage.html', {'engagements':engagements})

def login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None and user.is_authenticated:
            login(request, user)
            return redirect('Client:home')
        else:
            return render(request, 'Client/login.html', {'error':'Invalid Credentitals'})
    return render(request, 'Client/login.html')

def reportView(request):
    if request.method == 'POST':
        engagement_id = request.POST.get('submit')
        pivot = generatePivot(result_table_name = 'Result', client_table_name = 'Client Data', primary_key = 'Candidate ID')
        return render(request, 'Client/landing_page.html', pivot)
    return Http404()

# result_table_name = f'Result-{engagement_id}', client_table_name = f'Client Data-{engagement_id}'