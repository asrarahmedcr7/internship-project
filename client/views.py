from django.http import Http404
from django.conf import settings
from django.shortcuts import render
from .models import Client
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate
from django.shortcuts import redirect
from .utils import generateDateWisePivot, generateLocationWisePivot, generateGenderWisePivot, findAccuracy
import matplotlib
import matplotlib.pyplot as plt
matplotlib.use("Agg") 
import os

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

def overallAccuracyView(request):
    if request.method == 'POST':
        dateWisePivot = generateDateWisePivot(result_table_name = 'Result')
        genderWisePivot = generateGenderWisePivot(client_table_name = 'Client Data', result_table_name = 'Result', primary_key = 'Candidate ID')
        overall_count = {'True Positive':0, 'True Negative':0, 'False Positive':0, 'False Negative':0}
        on_date = None

        for date in dateWisePivot:
            on_date = date
            for observation in overall_count:
                overall_count[observation] += dateWisePivot[date][observation]
        overall_accuracy = findAccuracy(overall_count)
        print(overall_accuracy)

        dates = list(dateWisePivot.keys())
        accuracy_men = [genderWisePivot['Male'][date]['Accuracy'] for date in dates]
        accuracy_women = [genderWisePivot['Female'][date]['Accuracy'] for date in dates]
        
        plt.figure(figsize=(10, 5))
        plt.plot(dates, accuracy_men, label='Men', color='blue', marker='o', linestyle='--')
        plt.plot(dates, accuracy_women, label='Women', color='red', marker='o', linestyle='--')
        plt.xlabel('Date')
        plt.ylabel('Accuracy')
        plt.title('Accuracy Trend by Date and Gender')
        plt.legend()
        plt.grid(True)

        file_path = os.path.join(settings.MEDIA_ROOT, "dateGenderGraph.png")
        plt.savefig(file_path, format="png", dpi=100)
        plt.close()

        return render(request, 'Client/overallAccuracy.html', {'on_date':on_date, 'overall_accuracy':overall_accuracy, 'graph':'media/dateGenderGraph.png'})
    return Http404()


# result_table_name = f'Result-{engagement_id}', client_table_name = f'Client Data-{engagement_id}'