from django.http import Http404
from django.conf import settings
from django.shortcuts import render
from .models import Client
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login
from django.shortcuts import redirect
from .utils import generateDateWisePivot, generateLocationWisePivot, generateGenderWisePivot, findAccuracy, findTotal, findTNR
import matplotlib
import matplotlib.pyplot as plt
matplotlib.use("Agg") 
import os
from statistics import mean
from django.contrib.auth.views import LogoutView
from django.urls import reverse_lazy

@login_required(login_url='Client:login')
def homeView(request):
    client = Client.objects.get(username = request.user.username, password = request.user.password)
    engagements = client.engagements.all()
    return render(request, 'Client/homepage.html', {'engagements':engagements})

def ClientLogin(request):
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
        locationPivot = generateLocationWisePivot(client_table_name = 'Client Data', result_table_name = 'Result', primary_key = 'Candidate ID')
        overall_count = {'True Positive':0, 'True Negative':0, 'False Positive':0, 'False Negative':0}
        on_date = None

        gender_table = {}

        accuracies = []

        for gender in genderWisePivot:
            gender_table[gender] = {'True Positive':0, 'True Negative':0, 'False Positive':0, 'False Negative':0}

        for date in dateWisePivot:
            on_date = date
            for observation in overall_count:
                overall_count[observation] += dateWisePivot[date][observation]
                gender_table['Male'][observation] += genderWisePivot['Male'][date][observation]
                gender_table['Female'][observation] += genderWisePivot['Female'][date][observation]
            accuracies.append(dateWisePivot[date]['Overall Accuracy'])

        gender_table['Male']['Accuracy'] = findAccuracy(gender_table['Male'])
        gender_table['Male']['Total'] = findTotal(gender_table['Male'])
        gender_table['Female']['Accuracy'] = findAccuracy(gender_table['Female'])
        gender_table['Female']['Total'] = findTotal(gender_table['Female'])

        overall_accuracy = findAccuracy(overall_count)
        print(overall_accuracy)

        dates = list(dateWisePivot.keys())
        accuracy_men = [genderWisePivot['Male'][date]['Accuracy'] for date in dates]
        accuracy_women = [genderWisePivot['Female'][date]['Accuracy'] for date in dates]

        lower_limit = mean(accuracies) - 25
        dates_with_low_accuracy = []
        for date in dates:
            if dateWisePivot[date]['Overall Accuracy'] < lower_limit:
                dates_with_low_accuracy.append(date)
        
        plt.figure(figsize=(10, 5))

        plt.plot(dates, accuracy_men, label='Men', color='blue', linestyle='-', linewidth=3, alpha=0.7)
        plt.plot(dates, accuracy_women, label='Women', color='red', linestyle='-', linewidth=3, alpha=0.7)

        plt.xlabel('Date')
        plt.xticks(rotation=45)
        plt.ylabel('Accuracy')
        plt.title('Accuracy Trend by Date and Gender')
        plt.legend()
        plt.grid(True)
        plt.tight_layout()

        file_path = os.path.join(settings.MEDIA_ROOT, "dateGenderAccuracyGraph.png")
        plt.savefig(file_path, format="png", dpi=100)
        plt.close()

        return render(request, 'Client/overallAccuracy.html', {'on_date':on_date, 'overall_accuracy':overall_accuracy, 'graph':'media/dateGenderAccuracyGraph.png', 'location_table':locationPivot, 'gender_table':gender_table, 'dates_with_low_accuracy':dates_with_low_accuracy})
    return Http404()

def modelAccuracyView(request):
    if request.method == "POST":
        dateWisePivot = generateDateWisePivot(result_table_name = 'Result')
        genderWisePivot = generateGenderWisePivot(client_table_name = 'Client Data', result_table_name = 'Result', primary_key = 'Candidate ID')
        locationWisePivot = generateLocationWisePivot(client_table_name = 'Client Data', result_table_name = 'Result', primary_key = 'Candidate ID')

        location_table = dict.fromkeys(list(locationWisePivot.keys())[:3])
        for city in location_table:
            location_table[city] = {'RPN':locationWisePivot[city]['Risk Priority Number']}

        dates = [date for date in dateWisePivot]

        total_tn, total_fp = 0, 0
        for date in dates:
            total_tn += dateWisePivot[date]['True Negative']
            total_fp += dateWisePivot[date]['False Positive']

        overall_tnr = (total_tn * 100)// (total_tn + total_fp)

        tnr_men = [findTNR(genderWisePivot['Male'][date]) for date in dates]
        tnr_women = [findTNR(genderWisePivot['Female'][date]) for date in dates]
        tnr_dateWise = [dateWisePivot[date]['TNR'] for date in dates]

        tnr_mean = mean(tnr_dateWise)
        usl, lsl = tnr_mean + 25, tnr_mean - 25

        plt.figure(figsize=(10, 5))
        plt.plot(dates, tnr_men, label='Men', color='blue', linestyle='-', alpha=0.7)
        plt.plot(dates, tnr_women, label='Women', color='red', linestyle='-', alpha=0.7)
        plt.xlabel('Date')
        plt.ylabel('Specificity')
        plt.title('Specificity Trend by Date and Gender')
        plt.grid(True)
        plt.axhline(y=usl, color="r", linestyle="--", linewidth=1, label=f"Upper Limit ({usl})")
        plt.axhline(y=lsl, color="g", linestyle="--", linewidth=1, label=f"Lower Limit ({lsl})")
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.legend()

        file_path = os.path.join(settings.MEDIA_ROOT, "dateGenderSpecifictyGraph.png")
        plt.savefig(file_path, format="png", dpi=100)
        plt.close()

        return render(request, 'Client/modelAccuracy.html', {'overall_tnr':overall_tnr, "graph":'media/dateGenderSpecifictyGraph.png', 'on_date':dates[-1], 'location_table':location_table})
    return Http404()

def fairnessView(request):
    if request.method == "POST":
        genderWisePivot = generateGenderWisePivot(client_table_name = 'Client Data', result_table_name = 'Result', primary_key = 'Candidate ID')
        dates = [date for date in genderWisePivot['Male']]
        dpd = [abs(genderWisePivot['Male'][date]['Demographic Parity'] - genderWisePivot['Female'][date]['Demographic Parity']) for date in dates]

        plt.figure(figsize=(10, 5))
        plt.plot(dates, dpd, label='Demographic Delta', color='green', linestyle='-',linewidth=3, alpha=0.7)
        plt.xticks(rotation=45)
        plt.xlabel('Date')
        plt.ylabel('Demographic Delta')
        plt.title('Demographic Delta Trend by Date and Gender')
        plt.tight_layout()
        plt.legend()
        plt.grid(True)
        

        file_path = os.path.join(settings.MEDIA_ROOT, "dateGenderDemographicDeltaGraph.png")
        plt.savefig(file_path, format="png", dpi=100)
        plt.close()

        return render(request, 'Client/fairness.html', {'graph':'media/dateGenderDemographicDeltaGraph.png'})
    return Http404()


class ClientLogoutView(LogoutView):
    next_page = reverse_lazy('Client:home')
# result_table_name = f'Result-{engagement_id}', client_table_name = f'Client Data-{engagement_id}'