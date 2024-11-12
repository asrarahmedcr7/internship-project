from django.http import Http404
from django.conf import settings
from django.shortcuts import render
from .models import Client, ClientUser
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login
from django.shortcuts import redirect
from .utils import generateDateWisePivot, generateLocationWisePivot, generateGenderWisePivot, findAccuracy, findTotal, findTNR
import matplotlib
import matplotlib.pyplot as plt
matplotlib.use("Agg") 
import os
from statistics import mean,stdev
from django.contrib.auth.views import LogoutView
from django.urls import reverse_lazy

@login_required(login_url='Client:login')
def homeView(request):
    user = ClientUser.objects.get(username=request.user.username, password=request.user.password)
    
    # Access the associated client (it's already the instance, no need for 'pk=user.client')
    client = user.client  # This is the associated Client instance
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
        user = request.user
        client_id = user.client.id
        engagement_id = request.POST.get('engagement_id')

        request.session['engagement_id'] = engagement_id

        dateWisePivot = generateDateWisePivot(result_table_name = f'Result-{client_id}-{engagement_id}')
        genderWisePivot = generateGenderWisePivot(client_table_name = f'Client Data-{client_id}-{engagement_id}', result_table_name = f'Result-{client_id}-{engagement_id}', primary_key = 'Candidate ID')
        locationPivot = generateLocationWisePivot(client_table_name = f'Client Data-{client_id}-{engagement_id}', result_table_name = f'Result-{client_id}-{engagement_id}', primary_key = 'Candidate ID')
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

        dates = [date.day for date in dateWisePivot]

        accuracies_mean = mean(accuracies)
        lower_limit = 40
        
        plt.figure(figsize=(10, 5))

        plt.plot(dates, accuracies, label='Accuracy', color='blue', linestyle='-', linewidth=3, alpha=0.7)

        dates_with_low_accuracy = []
        for date, accuracy in zip(dates, accuracies):
            if accuracy < lower_limit:
                plt.plot(date, accuracy, 'ro')
                dates_with_low_accuracy.append(date)

        print(type(on_date))

        plt.xlabel('Date')
        # plt.xticks(rotation=45)
        plt.ylabel('Accuracy')
        plt.title('Accuracy Trend by Date')
        plt.axhline(y=lower_limit, color="r", linestyle="--", linewidth=1, label=f"Lower Limit-({lower_limit})")
        plt.axhline(y=accuracies_mean, color="g", linestyle="--", linewidth=1, label=f"Mean-({accuracies_mean})")

        plt.legend()
        plt.grid(True)
        plt.tight_layout()

        file_path = os.path.join(settings.MEDIA_ROOT, "dateAccuracyGraph.png")
        plt.savefig(file_path, format="png", dpi=100)
        plt.close()

        return render(request, 'Client/overallAccuracy.html', {'on_date':on_date, 'overall_accuracy':overall_accuracy, 'graph':'media/dateAccuracyGraph.png', 'location_table':locationPivot, 'gender_table':gender_table, 'dates_with_low_accuracy':dates_with_low_accuracy, 'engagement_id':engagement_id})
    return Http404()

def modelAccuracyView(request):
    if request.method == "POST":
        user = request.user
        client_id = user.client.id
        engagement_id = request.session.get('engagement_id')
        dateWisePivot = generateDateWisePivot(result_table_name = f'Result-{client_id}-{engagement_id}')
        genderWisePivot = generateGenderWisePivot(client_table_name = f'Client Data-{client_id}-{engagement_id}', result_table_name = f'Result-{client_id}-{engagement_id}', primary_key = 'Candidate ID')
        locationWisePivot = generateLocationWisePivot(client_table_name = f'Client Data-{client_id}-{engagement_id}', result_table_name = f'Result-{client_id}-{engagement_id}', primary_key = 'Candidate ID')

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

        tnr_mean = int(mean(tnr_dateWise))
        tnr_std = int(stdev(tnr_dateWise))
        usl, lsl = tnr_mean + (2 * tnr_std), tnr_mean - (2 * tnr_std)

        plt.figure(figsize=(10, 5))
        plt.plot(dates, tnr_men, label='Men', color='blue', linestyle='-', alpha=0.7)
        plt.plot(dates, tnr_women, label='Women', color='red', linestyle='-', alpha=0.7)
        tnr_outliers_male = []
        for date, tnr in zip(dates, tnr_men):
            if tnr < lsl or tnr > usl:
                plt.plot(date, tnr, 'bo')
                tnr_outliers_male.append(date)

        tnr_outliers_female = []
        for date, tnr in zip(dates, tnr_women):
            if tnr < lsl or tnr > usl:
                plt.plot(date, tnr, 'ro')
                tnr_outliers_female.append(date)
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
        user = request.user
        client_id = user.client.id
        engagement_id = request.session.get('engagement_id')
        genderWisePivot = generateGenderWisePivot(client_table_name = f'Client Data-{client_id}-{engagement_id}', result_table_name = f'Result-{client_id}-{engagement_id}', primary_key = 'Candidate ID')
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