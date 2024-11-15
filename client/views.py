from django.http import Http404
from django.conf import settings
from django.shortcuts import render
from .models import Client, ClientUser
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login
from django.shortcuts import redirect
from .utils import generateDateWisePivot, generateLocationWisePivot, generateGenderWisePivot, findAccuracy, findTotal, findTPR, findDemographicParity, fillLevels
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

def overallAccuracyView(request):
    if request.method == 'POST':
        user = request.user
        client_id = user.client.id
        engagement_id = request.POST.get('engagement_id')

        if engagement_id is None:
            engagement_id = request.session.get('engagement_id') #Setting engagement_id into session only when required

        request.session['engagement_id'] = engagement_id 

        # Retrieving required data for the view
        dateWisePivot = generateDateWisePivot(result_table_name = f'Result-{client_id}-{engagement_id}')
        genderWisePivot = generateGenderWisePivot(client_table_name = f'Client Data-{client_id}-{engagement_id}', result_table_name = f'Result-{client_id}-{engagement_id}', primary_key = 'Candidate ID')
        locationPivot = generateLocationWisePivot(client_table_name = f'Client Data-{client_id}-{engagement_id}', result_table_name = f'Result-{client_id}-{engagement_id}', primary_key = 'Candidate ID')

        # To store each observation's overall count
        overall_count = {'True Positive':0, 'True Negative':0, 'False Positive':0, 'False Negative':0}

        # The final date
        on_date = None 

        # To store gender wise overall observation count
        gender_table = {}

        # Date-wise accuracy list - to be used in the graph
        accuracies = []

        # Setting the count of each observation to zero for Male and Female
        for gender in genderWisePivot:
            gender_table[gender] = {'True Positive':0, 'True Negative':0, 'False Positive':0, 'False Negative':0}

        # Calculating overall count datewise and gender-wise
        for date in dateWisePivot:
            on_date = date # will be set to the final date when the loop ends

            for observation in overall_count:
                overall_count[observation] += dateWisePivot[date][observation] # datewise observation count
                # Gender-wise observation count
                gender_table['Male'][observation] += genderWisePivot['Male'][date][observation]
                gender_table['Female'][observation] += genderWisePivot['Female'][date][observation]

            # Date-wise accuracy list
            accuracies.append(dateWisePivot[date]['Overall Accuracy'])

        # Overall Accuracy and Total for each gender
        gender_table['Male']['Accuracy'] = findAccuracy(gender_table['Male'])
        gender_table['Male']['Total'] = findTotal(gender_table['Male'])
        gender_table['Female']['Accuracy'] = findAccuracy(gender_table['Female'])
        gender_table['Female']['Total'] = findTotal(gender_table['Female'])

        # Overall Accuracy datewise
        overall_accuracy = findAccuracy(overall_count)

        # list of dates - to be used to plot graph markers
        dates = [date for date in dateWisePivot]

        # list of dates - to be used to plot graph trend line
        graph_dates = [date.day for date in dateWisePivot]

        # Calculating mean of datewise accuracies
        accuracies_mean = int(mean(accuracies))

        # Pre-defined limit for the accuracy
        lower_limit = 40
        
        # Plotting the graph
        plt.figure(figsize=(10, 5)) # Defining height and width of the graph
        # Plotting the trendline - date vs accuracy
        plt.plot(graph_dates, accuracies, label='Accuracy', color='blue', linestyle='-', linewidth=3, alpha=0.7) 
        # Taking out dates on which the accuracy fell below the predefined limit
        dates_with_low_accuracy = []
        for date, accuracy in zip(dates, accuracies):
            if accuracy < lower_limit:
                plt.plot(date.day, accuracy, 'ro') # Marking the dates with a red marker
                dates_with_low_accuracy.append(date)
        # Labeling the graph
        plt.xlabel('Date')
        plt.ylabel('Accuracy')
        plt.title('Accuracy Trend by Date')
        # Plotting the limits and mean lines
        plt.axhline(y=lower_limit, color="r", linestyle="--", linewidth=1, label=f"Threshold-({lower_limit})")
        plt.axhline(y=accuracies_mean, color="g", linestyle="--", linewidth=1, label=f"Mean-({accuracies_mean})")
        # Legend gives the detail of each line in the graph
        plt.legend()
        plt.grid(True)
        plt.tight_layout()
        # Saving the generated graph in the media folder
        file_path = os.path.join(settings.MEDIA_ROOT, f"dateAccuracyGraph-{client_id}-{engagement_id}.png")
        plt.savefig(file_path, format="png", dpi=100)
        plt.close()
        # Rendering the respective template
        return render(request, 'Client/overallAccuracy.html', {'on_date':on_date, 'overall_accuracy':overall_accuracy, 'graph':'media/dateAccuracyGraph.png', 'location_table':locationPivot, 'gender_table':gender_table, 'dates_with_low_accuracy':dates_with_low_accuracy, 'engagement_id':engagement_id})
    return Http404()

def modelAccuracyView(request):
    def generate_graph(gender, tpr, clr): # Function to generate graph for each gender
        plt.figure(figsize=(10, 5))
        plt.plot(graph_dates, tpr, label=gender, color=clr, linestyle='-', alpha=0.7)
        plt.xlabel('Date')
        plt.ylabel('Sensitivity(%)')
        plt.title(f'Sensitivity Trend for {gender}')
        # Marking the dates on which the curve crossed the limits
        for date, tpr in zip(dates, tpr):
            if tpr < lsl[gender] or tpr > usl[gender]:
                plt.plot(date.day, tpr, 'bo' if clr == 'blue' else 'ro')
        plt.grid(True)
        plt.axhline(y=usl[gender], color="r", linestyle="--", linewidth=1, label=f"Upper Limit ({usl[gender]})")
        plt.axhline(y=lsl[gender], color="g", linestyle="--", linewidth=1, label=f"Lower Limit ({lsl[gender]})")
        plt.axhline(y=tpr_mean[gender], color="black", linestyle="--", linewidth=3, label=f"Mean ({tpr_mean[gender]})")
        plt.tight_layout()
        plt.legend()
        file_path = os.path.join(settings.MEDIA_ROOT, f"sensitivityTrend{gender}-{client_id}-{engagement_id}.png")
        plt.savefig(file_path, format="png", dpi=100)
        plt.close()
    
    def findGenderRPN(): # Function to calculate RPN based for each gender
        gender_table['Male']['Accuracy'] = findAccuracy(gender_table['Male'])
        gender_table['Male']['Total'] = findTotal(gender_table['Male'])
        gender_table['Female']['Accuracy'] = findAccuracy(gender_table['Female'])
        gender_table['Female']['Total'] = findTotal(gender_table['Female'])
        # Assigning Candidate Count Levels for both genders
        if gender_table['Male']['Total'] > gender_table['Female']['Total']:
            gender_table['Male']['Candidate Count Level'] = 2
            gender_table['Female']['Candidate Count Level'] = 1
        else:
            gender_table['Male']['Candidate Count Level'] = 1
            gender_table['Female']['Candidate Count Level'] = 2
        # Assigning Accuracy Levels for both genders
        if gender_table['Male']['Accuracy'] > gender_table['Female']['Accuracy']:
            gender_table['Male']['Accuracy Level'] = 2
            gender_table['Female']['Accuracy Level'] = 1
        else:
            gender_table['Male']['Accuracy Level'] = 1
            gender_table['Female']['Accuracy Level'] = 2
        # Calculating RPN for both genders
        gender_table['Male']['RPN'] = gender_table['Male']['Accuracy Level'] * gender_table['Male']['Candidate Count Level']
        gender_table['Female']['RPN'] = gender_table['Female']['Accuracy Level'] * gender_table['Female']['Candidate Count Level']
        # Returning the gender with high RPN
        if gender_table['Male']['RPN'] > gender_table['Female']['RPN']:
            return "Male"
        return "Female"

    if request.method == "POST":
        user = request.user
        client_id = user.client.id
        engagement_id = request.session.get('engagement_id')
        # Collecting required data
        dateWisePivot = generateDateWisePivot(result_table_name = f'Result-{client_id}-{engagement_id}')
        genderWisePivot = generateGenderWisePivot(client_table_name = f'Client Data-{client_id}-{engagement_id}', result_table_name = f'Result-{client_id}-{engagement_id}', primary_key = 'Candidate ID')
        locationWisePivot = generateLocationWisePivot(client_table_name = f'Client Data-{client_id}-{engagement_id}', result_table_name = f'Result-{client_id}-{engagement_id}', primary_key = 'Candidate ID')

        location_table = {} # Contains RPN for each location
        locations = list(locationWisePivot.keys())[:3]
        high_rpn_location = locations[0]
        for location in locations:
            location_table[location] = {}
            location_table[location]['RPN'] = locationWisePivot[location]['Risk Priority Number']

        dates = [date for date in dateWisePivot]
        graph_dates = [date.day for date in dates]

        total_tp, total_fn = 0, 0 # Overall True Positives and False Negatives to calculate Overall TPR
        gender_table = {}
        for gender in genderWisePivot:
            gender_table[gender] = {'True Positive':0, 'True Negative':0, 'False Positive':0, 'False Negative':0}

        for date in dates:
            total_tp += dateWisePivot[date]['True Positive']
            total_fn += dateWisePivot[date]['False Negative']

            for obs in gender_table['Male']:
                gender_table['Male'][obs] += genderWisePivot['Male'][date][obs]
                gender_table['Female'][obs] += genderWisePivot['Female'][date][obs]

        high_rpn_gender = 'Men' if findGenderRPN() == 'Male' else 'Women'

        overall_tpr = (total_tp * 100) // (total_tp + total_fn)

        tpr_men = [findTPR(genderWisePivot['Male'][date]) for date in dates]
        tpr_women = [findTPR(genderWisePivot['Female'][date]) for date in dates]

        # Finding Mean and Standard Deviations to calculate Upper and Lower Sensitivity Limits
        tpr_mean = {'Male':int(mean(tpr_men)), 'Female':int(mean(tpr_women))}
        tpr_std = {'Male':int(stdev(tpr_men)), 'Female':int(stdev(tpr_women))}
        usl = {'Male':tpr_mean['Male'] + (2 * tpr_std['Male']), 'Female':tpr_mean['Female'] + (2 * tpr_std['Female'])}
        lsl = {'Male':tpr_mean['Male'] - (2 * tpr_std['Male']), 'Female':tpr_mean['Female'] - (2 * tpr_std['Female'])}

        generate_graph('Male', tpr_men, 'blue')
        generate_graph('Female', tpr_women, 'red')

        return render(request, 'Client/modelAccuracy.html', {'overall_tpr':overall_tpr, "graph":{'Male':f'media/sensitivityTrendMale-{client_id}-{engagement_id}.png', 'Female':f'media/sensitivityTrendFemale-{client_id}-{engagement_id}.png'},  'on_date':dates[-1], 'high_rpn_location':high_rpn_location, 'high_rpn_gender':high_rpn_gender, 'location_table':location_table})
    return Http404()

def modelInclusivityView(request):
    if request.method == "POST":
        user = request.user
        client_id = user.client.id
        engagement_id = request.session.get('engagement_id')
        # Retrieving required data
        genderWisePivot = generateGenderWisePivot(client_table_name = f'Client Data-{client_id}-{engagement_id}', result_table_name = f'Result-{client_id}-{engagement_id}', primary_key = 'Candidate ID')
        locationWisePivot = generateLocationWisePivot(client_table_name = f'Client Data-{client_id}-{engagement_id}', result_table_name = f'Result-{client_id}-{engagement_id}', primary_key = 'Candidate ID')
        # (Demographic Parity, Location) list to get the location with highest DP
        location_wise_dp = [(findDemographicParity(locationWisePivot[location]), location) for location in locationWisePivot]
        higher_dp_location = max(location_wise_dp, key=lambda x : x[0])
        # Finding the datewise Demographic Parity Delta
        dates = [date for date in genderWisePivot['Male']]
        genderwise_total_obs = {'Male':{'True Positive':0, 'True Negative':0, 'False Positive':0, 'False Negative':0}, 'Female':{'True Positive':0, 'True Negative':0, 'False Positive':0, 'False Negative':0}}
        dpd = []
        for date in dates:
            dpd.append(abs(genderWisePivot['Male'][date]['Demographic Parity'] - genderWisePivot['Female'][date]['Demographic Parity']))
            for gender in genderwise_total_obs:
                for obs in genderwise_total_obs[gender]:
                    genderwise_total_obs[gender][obs] += genderWisePivot[gender][date][obs]
        # Finding the gender with higher demographic parity
        gender_dp = [(findDemographicParity(genderwise_total_obs[gender]), gender) for gender in genderwise_total_obs]
        higher_dp_gender = max(gender_dp, key = lambda x : x[0])
        # Finding the difference between DPD between the last week and current week
        dp_diff = dpd[-1] - dpd[-8]
        dpd_mean = int(mean(dpd))
        # Plotting the graph for DPD
        plt.figure(figsize=(10, 5))
        plt.plot([date.day for date in dates], dpd, label='Demographic Disparity', color='green', linestyle='-',linewidth=3, alpha=0.7)
        plt.gca().yaxis.set_major_locator(plt.MaxNLocator(integer=True))
        plt.xlabel('Date')
        plt.ylabel('Demographic Disparity')
        plt.axhline(y=dpd_mean, color="b", linestyle="--", linewidth=1, label=f"Mean-({dpd_mean})")
        plt.title('Demographic Disparity Trendline by Gender')
        plt.tight_layout()
        plt.legend()
        plt.grid(True)
        
        file_path = os.path.join(settings.MEDIA_ROOT, f"dateGenderDemographicDeltaGraph-{client_id}-{engagement_id}.png")
        plt.savefig(file_path, format="png", dpi=100)
        plt.close()

        return render(request, 'Client/modelInclusivity.html', {'graph':f'media/dateGenderDemographicDeltaGraph-{client_id}-{engagement_id}.png', 'higher_dp_location':higher_dp_location[1], 'location_dp_value':higher_dp_location[0], 'higher_dp_gender':'Men' if higher_dp_gender[1] == 'Male' else 'Women', 'gender_dp_value':higher_dp_gender[0], 'dp_diff':dp_diff })
    return Http404()

def aboutView(request):
    return render(request, 'Client/about.html')

class ClientLogoutView(LogoutView):
    next_page = reverse_lazy('Client:home')